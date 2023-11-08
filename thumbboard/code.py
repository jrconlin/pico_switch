"""
Micro Switch doo-hickey

This uses a PicoW board that monitors MQTT and looks for messages
to indicate what button to press. This is all VERY insecure, so
please don't use this on a public facing network.

This uses two files:
1) `settings.toml` which contains the various environment
    variables I used below.
2) `switches.json` which contains a JSON formatted
    dictionary of switch values (see below)

Hint: While fiddling with this, probably not a bad idea to run the
Mu Python Serial connection to monitor stdout.

"""
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import board
import binascii
import busio
import digitalio
import gc
import ipaddress
import json
import os
import socketpool
import terminalio
import time
import wifi

# just to make things easier later, define some constants.
MQTT_HOST = os.getenv("MQTT_HOST", "10.10.1.110")
MQTT_USER = os.getenv("MQTT_USER", "username")
MQTT_PASS = os.getenv("MQTT_PASS", "Pa55W0rd")
MQTT_PUB = os.getenv("MQTT_PUB", "pico/switch")

WIFI_SSID = os.getenv("WIFI_SSID")
WIFI_PASS = os.getenv("WIFI_PASSWORD")
# Optional: See below if you want to skip DHCP


class SwitchException(Exception):
    """Minimal exception for us to abuse."""

    pass


def get_pool():
    """Connect to wifi

    It can take several attempts before the device successfully logs in the first time

    """
    # Dump the local mac address in case you want to see if it's showing
    # up in your router logs. (I saw that I was connecting, but getting a
    # bad DHCP address).
    print("# Mac Addr: " + binascii.hexlify(wifi.radio.mac_address).decode())
    print(f"{WIFI_SSID}::{WIFI_PASS}")
    wifi.radio.connect(ssid=WIFI_SSID, password=WIFI_PASS)
    print("# connected to WiFi")
    # Force us to a specific WiFi address
    if os.getenv("LOC_ADDR"):
        print(f"# Setting addr {wifi.radio.ipv4_address}")
        wifi.radio.set_ipv4_address(
            ipv4=ipaddress.ip_address(os.getenv("LOC_ADDR")),
            netmask=ipaddress.ip_address(os.getenv("LOC_MASK")),
            gateway=ipaddress.ip_address(os.getenv("LOC_GATE")),
            ipv4_dns=ipaddress.ip_address(os.getenv("LOC_DNS")),
        )
    # Test to see if you can reach the MQTT host.
    if wifi.radio.ping(ipaddress.ip_address(MQTT_HOST)):
        print("# Can access MQTT host")
    else:
        raise SwitchException("!! Could not find MQTT Host")
    pool = socketpool.SocketPool(wifi.radio)
    return pool


def on_connect(client, _userdata, _flags, _rc):
    """Get all the events, we can parse out the more interesting ones"""
    print(f"# Connected to MQTT, subscribing to {MQTT_PUB}...")
    client.subscribe(MQTT_PUB)


def on_message(client, _topic, msg):
    """Handle an incoming MQTT message"""
    msg = msg.decode()
    print(f"# msg: {msg}")

    switch = client._user_data.get(msg)
    if switch is None:
        print(f"!! Unknown switch {msg}")
        return

    print(f"# toggling {msg} switch")
    switch["switch"].value = True
    time.sleep(switch["duration"])
    switch["switch"].value = False


def init_mqtt(switches):
    """Do the initial connection to MQTT"""
    # Get an internet connection from the local pool
    pool = get_pool()
    user = MQTT_USER
    passw = MQTT_PASS
    print(f"# Connecting to... {user}:{passw}@{MQTT_HOST}")
    client = MQTT.MQTT(
        broker=MQTT_HOST,
        username=user,
        password=passw,
        socket_pool=pool,
        use_binary_mode=True,
        user_data=switches,
    )
    # Set the various callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect()
    print("# Connected to MQTT, waiting for messages")

    # Show how much memory is available. (it's not a lot.)
    s = os.statvfs("/")
    print(f"# Memory: {gc.mem_alloc()} of {gc.mem_free()} storage:{s[0]*s[3]/1024}KB")
    while True:
        client.loop()


# main
print("# Mac Addr: " + binascii.hexlify(wifi.radio.mac_address).decode())
attempt = 0
## It can take several attempts before we actually connect.
while True:
    try:
        if attempt > 10:
            raise SwitchException("!!Cannot Connect")
        pool = get_pool()
        break
    except ConnectionError as e:
        attempt = attempt + 1
        print(attempt)

# ok, now pull the switch definitions out of the switches file.
# This file contains a JSON dictionary of the various switches we want to support
# e.g.
#   ```json
#    {
#       "garage":{"switch":"GP14", "duration": 0.5},
#       "alarm":{"switch":"GP12"}
#    }
#   ```
# This file says that we want "garage" to trigger whatever is connected to GP14
# for half a second and for "alarm" to trigger whatever is connected to GP12 for
# the default full second.
# (Remember, each device has to make a circuit to GND to work.)
#


def dit(led):
    """Blink the LED for a short morse code 'Dit'"""
    led.value = True
    time.sleep(0.25)
    led.value = False
    time.sleep(0.25)


def dash(led):
    """Blink the LED for a long morse code 'Dash'"""
    led.value = True
    time.sleep(1)
    led.value = False
    time.sleep(0.25)


with open("switches.json") as switch_file:
    switches = json.load(switch_file)
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    for key in switches.keys():
        val = switches.get(key)
        if val.get("pin"):
            pin = getattr(board, val.get("pin"))
            switch = digitalio.DigitalInOut(pin)
            switch.direction = digitalio.Direction.OUTPUT
            switches[key] = {"switch": switch, "duration": val.get("duration", 1.0)}
    try:
        init_mqtt(switches)
    except SwitchException:
        while True:
            # Something bad, show an SOS.
            for x in range(0, 3):
                dit(led)
            for x in range(0, 3):
                dash(led)
            for x in range(0, 3):
                dit(led)
            time.sleep(2)
    except Exception:
        # Something REALLY bad, show the slow blink of death.
        while True:
            led.value = True
            time.sleep(2)
            led.value = False
            time.sleep(2)
