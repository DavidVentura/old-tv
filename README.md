# Resurrecting an old TV


## Idea

### Channels

The idea is to have each channel dedicated to a purpose and to iterate between programs.

If you select channel 3 this'd iterate between program 0 and 1 (there are only 2 programs on channel 3)


### Ads

After each program is finished, a random ad should play.


## Hardware

### Original TV

![Back](/images/back.jpg)

![Front](/images/front.jpg)

![Insides](/images/insides.jpg)

### Hack

I'm using a Raspberry Pi, a composite to VHF converter and the tv.
I'm going to remove the TV tuner and glue it to be permanently on channel 3 (The frequency used by the VHF converter).

![back](/images/selector-back.jpg)

![side](/images/selector-side.jpg)

Then I'm going to put an input selector where the original channel knob was and wire that directly to the Pi.

## Software

This repo contains all the software required which is mostly glue and:

* Gstreamer for playback
* sqlite to store channel status
