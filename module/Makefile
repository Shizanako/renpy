# This makefile should work on Linux, and might work on other unix-like
# platforms as well. It probably won't work on Mac OS X, however.

build:: _renpy.c sound.c nativemidi.c winmixer.c 

clean:
	-rm *.so pysdlsound/*.so
	-rm -Rf build

%.c : %.pyx
	pyrexc $+