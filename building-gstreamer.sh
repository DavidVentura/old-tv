#!/bin/bash
#To be run on the pi
set -euo pipefail
v="1.11.1"

# Other deps? Maybe required for the pi
# xz-utils libtool-bin libglib3.0-cil libglib2.0-dev liborc-0.4-dev liborc-0.4-0 libgles2-mesa libegl1-mesa libegl1-mesa-dev libgl1-mesa-dev libgl1-mesa-glx libgles2-mesa mesa-utils-extra libgles2-mesa libgles2-mesa-dev sudo

# You need 
# gst-libav-1.11.1
# gst-omx-1.11.1
# gst-plugins-bad-1.11.1
# gst-plugins-base-1.11.1
# gst-plugins-good-1.11.1
# gstreamer-1.11.1
# You can get it here 
# https://gstreamer.freedesktop.org/src/

export CFLAGS="-I/opt/vc/include -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux/ -I/opt/vc/include/IL"
export LDFLAGS="-L/opt/vc/lib"
export CPPFLAGS="-I/opt/vc/include -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux -I/opt/vc/include/IL"
export LIBS="-L/opt/vc/lib"

apt install -y autoconf autopoint libtool bison flex libgstreamer1.0-dev yasm liborc-0.4-dev librtmp-dev gnutls-bin libx264-dev eatmydata

emd='/usr/bin/eatmydata'
v=1.11.1

core() {
cd gstreamer-$v
$emd ./autogen.sh --enable-maintainer-mode --disable-{gtk-doc,nls,docbook,tests,benchmarks,examples,debug,debugutils} --enable-failing-tests --disable-loadsave --enable-poisoning
$emd make -j5
sudo $emd make install
cd ..
}

base(){
cd gst-plugins-base-$v
$emd ./autogen.sh --enable-{maintainer-mode,experimental} --disable-{gtk-doc,nls,docbook,orc,examples,tests,ogg,oggtest,vorbis,vorbistest,speex,freetypetes}
$emd make -j5
sudo $emd make install
cd ..
}

good(){
cd gst-plugins-good-$v
$emd ./autogen.sh --enable-maintainer-mode --disable-{nls,gtk-doc,docbook,debug,debugutils,examples,tests,aalibtest} --disable-apetag --disable-audiofx --disable-auparse --disable-cutter --disable-effectv --disable-interleave --disable-flx --disable-goom --disable-goom2k1 --disable-imagefreeze --disable-law --disable-level --disable-monoscope --disable-multifile --disable-multipart --disable-replaygain --disable-shapewipe --disable-spectrum --disable-y4m --disable-oss --disable-oss4 --disable-sunaudio --disable-osx_audio --disable-osx_video --disable-x --disable-xshm --disable-aalib --disable-aalibtest --disable-annodex --disable-cairo --disable-cairo_gobject --disable-esd --disable-esdtest --disable-flac --disable-gconf --disable-gdk_pixbuf --disable-jack --disable-jpeg --disable-libcaca --disable-{libdv,libpng,dv1394,shout2,soup,taglib,wavpack,removesilence,videofilters,sdp,jpegformat,asfmux}
$emd make -j5
sudo $emd make install
cd ..
}

bad() {

cd gst-plugins-bad-$v
$emd ./configure --enable-maintainer-mode --disable-{static,nls,gtk-doc,docbook,debug,debugutils,tests,examples} --disable-fatal-warnings --enable-experimental --disable-audiovisualizers --disable-bayer --disable-cdxaparse --disable-dccp --disable-dtmf --disable-dvbsuboverlay --disable-dvdspu --disable-faceoverlay --disable-festival --disable-fieldanalysis --disable-freeze --disable-freeverb --disable-frei0r --disable-gaudieffects --disable-geometrictransform --disable-hls --disable-inter --disable-ivfparse --disable-jp2kdecimator --disable-liveadder --disable-mve --disable-mxf --disable-nsf --disable-nuvdemux --disable-patchdetect --disable-pcapparse --disable-pnm --disable-scaletempo --disable-sdi --disable-segmentclip --disable-siren --disable-smooth --disable-speed --disable-subenc --disable-tta --disable-vmnc --disable-y4m --disable-directsound --disable-wasapi --disable-direct3d --disable-directdraw --disable-direct3d9 --disable-directshow --disable-android_media --disable-apple_media --disable-osx_video --disable-shm --disable-vcd --disable-opensles --disable-assrender --disable-voamrwbenc --disable-voaacenc --disable-apexsink --disable-cdaudio --disable-celt --disable-chromaprint --disable-cog --disable-dc1394 --disable-decklink --disable-dirac --disable-dts --disable-resindvd --disable-faac --disable-faad --disable-flite --disable-gsm --disable-jp2k --disable-liveadder --disable-ladspa --disable-lv2 --disable-libmms --disable-linsys --disable-modplug --disable-mimic --disable-mplex --disable-musepack --disable-musicbrainz --disable-mythtv --disable-nas --disable-neon --disable-ofa --disable-openal --disable-opencv --disable-opus --disable-pvr --disable-rsvg --disable-timidity --disable-teletextdec --disable-wildmidi --disable-sdl --disable-sdltest --disable-sndfile --disable-soundtouch --disable-spc --disable-gme --disable-vp8 --disable-swfdec --disable-dvb --disable-wininet --disable-acm --disable-dash --disable-vdpau --disable-schro --disable-zbar --disable-spandsp --disable-gsettings --disable-schemas-compile --disable-sndio --disable-opengl --enable-gles2 --enable-egl --disable-glx --disable-x11 --disable-wayland --enable-dispmanx --with-gles2-module-name=/opt/vc/lib/libGLESv2.so --with-egl-module-name=/opt/vc/lib/libEGL.so

$emd make -j5
sudo $emd make install
cd ..

}

build_ffmpeg() {
cd gst-libav-$v
$emd ./autogen.sh --disable-{fatal-warnings,gtk-doc,debug,debugutils,tests,examples}
$emd make -j5
sudo $emd make install
cd ..
}

omx() {
cd gst-omx-$v
$emd ./autogen.sh --with-omx-target=rpi --disable-{fatal-warnings,gtk-doc,debug,debugutils,tests,examples} --with-omx-header-path=/opt/vc/include/IL
$emd make -j5
sudo $emd make install
cd ..
}


core
base
good
bad
omx
build_ffmpeg
