# Pico Switch

Make your dumb devices smarter.

This is kind of a crappy hack, and it was made out of spite, but it works.

## The dumb idea

There are a lot of "dumb" and "stupid" devices. A "dumb" device is one that may not have connection to the internet. A "stupid" device is one that is connected to the internet, but forces you to use a phone app for inexplicable reasons.

Many of the thing associated with these "dumb" or "stupid" devices have cheap remote controls. Even better, they often have cheaper replacement remote controls that you can get at hardware stores for far cheaper than the "official" ones.

So let's say you have a "stupid" device like [a garage door made by a Major Manufacturer like MyQ](https://arstechnica.com/gadgets/2023/11/chamberlain-blocks-smart-garage-door-opener-from-working-with-smart-homes/) that now insists that everyone use their phone app instead of a proper web app or API. Well, what someone could do would be to pop on down to the local hardware store and by [a cheap Garage Door remote](https://www.amazon.com/dp/B098SP6RJ9/) for $15, and a [Pico W](https://www.amazon.com/dp/B0C4TRR6VT/) or an [ESP32](https://www.amazon.com/dp/B08D5ZD528/) for $12 or so. Grab the trusty soldering iron and run a couple of leads from the switch on the remote to a GPIO and GND connector on the thumb board, then run this script using [CircuitPython 8](https://circuitpython.org/downloads)

Since the thumb board isn't supplying power to the remotes, you can even wire up a bunch of different remotes to the same thumb board and control a bunch of different devices.

## Installation

Once you've got CircuitPython installed on the device, you should be able to just copy the contents of `thumbboard` to your thumbboard, change the values of `settings.toml` and `switches.json` to be less made-up and be good to go.

You might want to verify that the files in `/lib` are correct, but you kinda have to dig through the various [Bundles](https://circuitpython.org/libraries) particularly the Community Bundle. I included them here because I want to be nice.

## Connecting to HomeAssistant

The next bit would be to run MQTT to act as a message server between HomeAssistant and the thumb board.

This is actually pretty easy. Once you've [enabled MQTT](https://www.home-assistant.io/integrations/mqtt), you can go under
`Settings` > `Automations & scenes` > `Scripts` and click the ( + ADD SCRIPT ) button.
You can "Create a new script from scratch" if you like, give it a name and [ + ADD ACTION ] > `Call Service`
The service should be `mqtt.publish` and then

Topic: `pico/switch`

☑ Payload: _whatever your switch controls, e.g. `garage`_

☑ QoS: 0

And then hit ( 🖬 SAVE SCRIPT )

You can then create a [button](https://www.home-assistant.io/dashboards/button/) on the Overview that calls a [Tap Action](https://www.home-assistant.io/dashboards/actions/#tap-action) with the action set to `call-service` with service set to `script.`_your script name here_
