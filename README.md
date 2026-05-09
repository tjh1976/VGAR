# VGAR

Very Good Atari Remote - An PC Atari 8 bit Game loader and control system for use with real 8 bit hardware



# Overview and Usage

VGAR is a Python based program that acts as a Front end Loader for 8 bit Atari Games and other software, using RespecQT and a USB SIO device to allow loading of the software directly on the Atari.

It additionally has features designed to interoperate with modern commonly installed Atari 8 bit upgrades, namely AKI USB and Ultimate 1MB.  If you have those devices installed, you can use this software to completely control and automate both loading of software on the Atari, and control of keyboard input from your PC, allowing typing and use of (most) Atari special keys.  The catch however is we need a go-between, and for this I have used an Arduino Uno R3 board to allow VGAR to 'speak' to the Atari by providing a HID passthrough in place of a keyboard you would normally attach to your Atari's AKI USB Port.  As the Arduino's USB then connects to the Atari, VGAR speaks to that via a PC USB TTL adapter.

There may be better ways to do this with alternate hardware, however the two additional devices required are available very cheaply, so these are what VGAR is designed to use.
In theory alternate hard methods could be used if same/similar code was used to pass through HID codes via USB.  VGAR will just blindly send to the serial interface.

Once all prerequisites are handled, and you launch VGAR-Beta-0.\*(\*\*\*).py , you are met with the main VGAR interface, after a short pause.  Here you can opt to either manually browse your Atari software collection and choose an image to load, or you can click "Random Filename" to give you a random game choice from a random pool of 100 games selected from your archive.  If you don't like any of them, you can click "Load Batch" to grab another selection which will be cycled through by the "Random Filename" function.

When a game is selected, if available, it's cover image / screenshot image is also displayed (if it is in same directory with same base name as the game file).  At this point, the path is available via the Copy button, should you wish to browse there, or load it manually via RespeQT, however if correctly configured, you can either click "Mount in RespeQT" to automatically load a RespecQT session with the file ready to load, bypassing need to use RespeQT's own GUI.  If you have the Serial to Arduino to Atari interface configured, and you are lucky enough to have an Ultimate 1MB installed, you can click "Auto Launch", and the Atari will cold boot and load the game.  This is achieved via a number of automated keypresses sent and handled by the U1MB's BIOS screens.  Once rebooted, the auto-mounted file in RespecQT will start to load.

So this is a 100% hands off front end software loader for an 8 bit Atari.

It is also a full remote keyboard controller, via the USB AKI interface.

If you click the Control button you are presented with an image of an Atari keyboard.  All keys on the keyboard are clickable, and will send the appropriate HID code through the interface to the Atari.  If you want to freehand type text , you can click into the text box at the base, type and click "String Send" to send it.  Alternatively, click "Key Capture" and everything you type will be instantly sent to the Atari until you press the Escape key, which cancels keyboard capture.  (Note if you find issues with speed / key detection, play with debounce setting in the INI file).

Another small feature left behind from development / debug is a small field that can send HID codes directly to the Atari AKI USB either in decimal eg 29, or hex as eg 0x1D, and get the corresponding character, in this case, Z.

If you want to hold down a key on the Atari, hold CTRL on you PC and click it on the Atari image.  A normal key click will release holds.

Back to the main menu, while you use the software to browse through your Atari collection you may wish to record games you like and dislike.  Well there are buttons for that, and the loaded file will be recorded in relevant lists, viewable by clicking the "Rating DB" button.  On the lists, you can load a game back by double-clicking on it later.

Lastly there are 6 Preset buttons to the left and the right where you can save your favourite games.  Hold CTRL and click a button to load the current file to a preset.  Click it normally to load it back.

I will be putting a setup and usage video on my Youtube Channel, should anyone be crazy enough to want to try this project for themselves :)

# Why did I do this?

Good question.  It started with a small DOS batch script to randomly select a game to try out on my Youtube Channel.  Then I started to play around with something that would look a bit more interesting to present the random selection graphically.  Had worked on a few things recently in Python, so seemed like a good idea to use that.  The idea to control an Atari via AKI USB was a separate idea / project I was looking at using a Raspberry Pi as a HID interface.  Due to various challenges, I eventually tried the same with an Arduino board I had and made quick progress for remotely controlling an Atari.  Separately, I had figured I could load software semi-autonomously by manipulating RespecQT session files and loading via SIO2USB, and well, it all started coming together as one thing.

The origins of this project started over a year ago, and lapsed somewhat due to other life issues, but more recently I've put in more time to put this stupid thing to bed.

Interested to know what others may get out of this (if anything!), and whether it's used with other upgraded Atari's to make the most of all the features.  Any and all feedback is welcome, and will help me improve the software.

If you find VGAR useful and would like to support future development, you can buy me a coffee here: https://buymeacoffee.com/tjatarian



# VGAR BETA 0.1 Release notes

Loading of ATR or XEX files on Atari requires install of RespecQT.  Version tested : RespeQt-r5.3-64bits
Use with SIO2PC USB  : https://retrolemon.co.uk/atari-8bit-storage-devices/38-sio2pc-usb.html or equivalent device.
You need to create a subfolder called XEX to contain a target XEX loader file "VGAR.xex" which is copied over with each loaded XEX.
Example Path used for Testing D:\\VGAR\\VGAR-Program\\xex

Use to control Atari keyboard requires an 8 bit Atari upgrades with the AKI USB Keyboard Interface :
https://retrolemon.co.uk/atari-8bit-upgrades/130-aki-usb-keyboard-interface.html

# Games Archive

While testing the beta, I used the Fandal and Homesoft Atari archives, copied to D:\\VGAR\\AtariGames
The location should be editable in the INI file
You should be able to use any collection of Atari ATR and XEX files, in any number of sub-folders.

# RespecQT

For RespecQT Configuration, you need to update DOS\_XEX.respeqt so that D0 points to mypcdoss1.atr, and D0 points to the XEX subfolder
Please ensure to select MYDos mode for the folder mount.

For testing this beta, RespecQT was installed to D:\\VGAR\\RespeQt-r5.3-64bits ,
though if you edit the INI, you should be able to install it anywhere, unless I've done something wrong.

# Python

VGAR Beta 0.1 was developed and tested with Python 3.13.7(64 bit)

Once installed to setup python for VGAR, use this to load required modules:

pip install -r requirements.txt



# Arduino Uno R3 Setup for communication with Atari via AKI USB

This requires some familiarity with programming an Arduino via it's IDE Software.
Additionally you need to be familiar with use of the Flexible In-System Programmer (FLIP) Tool to update it's firmware,
and know appropriate pins to jump to put device into DFU programming mode.

To setup the Arduino, load the provided sketch via the Arduino IDE Software, then after ensuring you have a valid flash image for recovery,
such as UNO-dfu\_and\_usbserial\_combined.hex

https://github.com/arduino/ArduinoCore-avr/blob/master/firmwares/atmegaxxu2/UNO-dfu\_and\_usbserial\_combined.hex

Put the device into DFU mode and use Flip to flash Adrino-keyboard-0.3.xex image to the device

https://github.com/coopermaa/USBKeyboard/blob/master/firmware/Arduino-keyboard-0.3.hex

This makes the Arduino a USB HID passthrough device that can receive HID codes directly from the VGAR python program to control the Atari.
As the USB on the Arduino has to be connected to the ATARI, HID codes must be sent to it via it's TTL TX/RX interface,
connected to the PC using a basic USB Serial TTL device.

Though standard keyboard signalling will function, some more advanced auto-launch features require an Atari Upgraded with an Ultimate 1MB.

# INI File

The INI file can be edited in Notepad, and looks like this:

\#The Atari ATR and XEX File Location:
atari\_files = D:/VGAR/AtariGames

\#Location of Database of games stored as good/bad
db\_location = D:\\VGAR\\VGAR-Program\\db.json

\#Path of your Respecqt Installation
respecqt\_path = D:\\VGAR\\RespeQt-r5.3-64bits\\RespeQt\\RespeQt.exe

\#Path where our controlled Respecqt session files are located
session\_path = D:\\VGAR\\Random\_Atari\_Game.respeqt

\#Key Debounce interval - can be adjusted if have typing issues
debounce\_interval = 0.05

\#Location of temp image used when no game image found
placeholder\_image = D:\\VGAR\\VGAR-Program\\placeholder.png

\#Startup sound file
vgar\_start\_sound = "vgar-start.wav"

\#Game load sound file
vgar\_load\_sound = "cload.wav"

\#COM Port for TTL Device to Adruino
com\_port=COM5
#Baud rate for TTL
baud=9600
#Delay before pressing key in DOS to load XEX (Long delay here as seems getting low SIO rates for RespecQT and may need to change cable / replace device)
xexload\_delay=15

Following this are Game Pre-sets.  You can delete the sample entries, and a blank list will be recreated on first run

# Prerequisite Summary

Noting, deviations from stated versions may be possible, but not tested so experiences may vary.
This summary is for FULL functionality.  Items with \* are optional for full control.

\*Install ARDUINO\_HID\_PASSTHROUGH\_CODE\_BETA\_0.1 Sketch on Arduino
\*Flash Adrino-keyboard-0.3.xex on Arduino
\*Connect PC USB TTL Device to Arduino Serial TX/RX Pins
Copy VGAR Beta 0.1 files to Install path - Recommend D:\\VGAR\\VGAR-PROGRAM
Copy Atari Files to Appropriate path - Recommend D:\\VGAR\\AtariGames
Install Python3.13.7
pip install -r requirements.txt
Install RespeQt-r5.3-64bits - Recommend to D:\\RespeQt-r5.3-64bits
Edit INI for your paths
Run VGAR-Beta-0.1(112).py

# External Requirements

https://github.com/RespeQt/RespeQt/releases
https://www.python.org/downloads/
https://retrolemon.co.uk/atari-8bit-upgrades/130-aki-usb-keyboard-interface.html
https://docs.arduino.cc/software/ide/
https://www.microchip.com/en-us/development-tool/flip
https://github.com/arduino/ArduinoCore-avr/blob/master/firmwares/atmegaxxu2/UNO-dfu\_and\_usbserial\_combined.hex
https://github.com/coopermaa/USBKeyboard/blob/master/firmware/Arduino-keyboard-0.3.hex
Example Uno R3 Board : https://www.amazon.co.uk/UNO-Board-Rev3-ATMEGA328P-CH340G/dp/B0CY9Q7YN2/
Example TTL Board : https://www.amazon.co.uk/CP2102-Serial-Converter-Module-Dupont/dp/B07XRF152K
(Not one I used - cannot find where I got it, but should work the same)

My Pico Dos (for use loading XEX files via RespecQt : http://www.horus.com/\~hias/atari/mypdos-4.06.zip

If you find VGAR useful and would like to support future development, you can buy me a coffee here: https://buymeacoffee.com/tjatarian
Youtube Video to follow with further information





# VGAR BETA 0.2 Release notes



No sooner had I released this, I notice an annoying regression I had not spotted.  When cycling through random games, the previous games image was left displayed, not the correct one.  Was missing a single call to display the final image.  Now fixed.

