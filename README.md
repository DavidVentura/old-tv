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

### Building Gstreamer

Use gst-uninstalled:

Install deps:

```bash
sudo apt-get build-dep gstreamer1.0-plugins-{base,good,bad,ugly}
sudo apt-get install autoconf autopoint libtool bison flex libgstreamer1.0-dev yasm liborc-0.4-dev libx264-dev git-core libegl1-mesa-dev libgles2-mesa-dev python-gi-dev python-dev python3-dev
wget https://cgit.freedesktop.org/gstreamer/gstreamer/plain/scripts/create-uninstalled-setup.sh
# As this doesn't clone gst-omx you have to edit the script and add it yourself
# I also removed gst-libav
# Now you have to cd into every directory (first gstreamer, then gst-plugins-base, then the rest) and run ./autoconf.sh && make -j5
# I had to run 
# ./configure CFLAGS=-I/opt/vc/include -I /opt/vc/include/interface/vcos/pthreads -I /opt/vc/include/interface/vmcs_host/linux/ LDFLAGS=-L/opt/vc/lib --disable-gtk-doc --disable-opengl --enable-gles2 --enable-egl --disable-glx --disable-x11 --disable-wayland --enable-dispmanx --with-gles2-module-name=/opt/vc/lib/libGLESv2.so --with-egl-module-name=/opt/vc/lib/libEGL.so
# under gst-plugins-bad
#
# and ./autogen.sh --with-omx-header-path=/opt/vc/include/IL --with-omx-target=rpi
# under gst-omx
```


### Blank the tty

Blanking the tty

```bash
#!/bin/bash
setterm -reset -cursor off | sudo tee /dev/tty1 > /dev/null
```

Turning the screen on
```bash
echo -ne "\033[9;0]" | sudo tee /dev/tty1
```

Disabling graphical warnings (lighting bolt) (fix your psu!)

```
grep -q '^avoid_warnings=1' /boot/config.txt || (echo 'avoid_warnings=1' | sudo tee -a /boot/config.txt)
```


### config.txt

http://elinux.org/RPiconfig

```
sdtv_mode=0    # Normal NTSC
# sdtv_mode=2    Normal PAL
sdtv_aspect=1  # 4:3
# sdtv_aspect=2  14:9
# sdtv_aspect=3  16:9

gpu_mem=128
avoid_warnings=1
initial_turbo=60
```
