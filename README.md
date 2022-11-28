Pellet Stove conversion to ESPHome.

This project dives deep into the TuyaMCU parts of ESPHome for various pellet stoves.  While the TuyaMCU implementation is robust, getting information on what it does and how it does it and why has been challenging to say the least.  I hope this helps someone else.
See the issues section for mods, and explanations of various parts of these stoves.

TuyaMCU Docs. https://esphome.io/components/tuya.html

The Tuya TYWE1S chips and those like it are basically just repackaged ESP8266 modules.  All the functions of the 8266 are all there.  TuyaMCU provides an abstraction layer between the display/control until and ESPHome. It allows control messages to be both Sent and Received from the device the module is controlling.

I'm an electronic engineer/designer by education and training, not a programmer.  When chips are soldered in place on a commercial circuit board and each pin has a live trace going to and from it, then we, as trained engineers, MUST assume that those pins are being used for some purpose, hence, likely not available for use.  but...

That said, I LOVE hacking this stuff and just because a trace is there doesnt mean the pin cant be used.  Best practice is to ground unused inputs and outputs with or without current limiting resistors.  However, in the case of multilayer PCBs, it is next to impossible for the average person to know what or how to trace those pins.  But, often they can be used.  More on this later.

We start with replacing the buggy, error prone Tuya control software in the TYE1S control chip in my Wood Pellet Stove with ESPHome.

**Product Models:** 
Cleveland Ironworks Wood Pellet Stove (there are 4 models, all use the same controller).  
I have a test bench set up with a spare control board. i have 2 models of this stove which both fail, but for different reasons.

It also appears from the Wifi module (N12210) that this exact same controller is used in Nemaxx Pellet Stove Pellet Heater P6 P9 P12.  https://www.ebay.com/itm/193755684864

Masterforge has the exact same models of this stove, all will use the same controller.

Ther are several others sold by Lowes, and other retailers that use the same display control board and TYWE1S chip.

There are a few displays that look slightly different but I believe all have the same internals.
![image](https://user-images.githubusercontent.com/52110065/201829440-4ba185fc-b787-47f6-98dc-5aa7e67d9064.png)
<img width="738" alt="image" src="https://user-images.githubusercontent.com/52110065/201829503-b268795e-132c-4b8f-9ec9-96a7dc361b03.png">

They work ok most of the time, but the stove malfunctions fairly frequently.  
Common mafunctions include:
- randomly turning off w/ the msg "Goodbye!" on the display.
- pellets failing to light in the hopper
- not coming back on after power failure
- various cryptic E messages from time to time. E1,E2,ESC1, ESO1,ESC2,ESO2,etc  

**Problem**
Pellet stoves made by Cleveland Ironworks all use the TuyaMCU chip TYWE1S to communicate with the stove's MCU inside the display unit.  Their shoddy programmer defined multiple datapoints for the same attribute in at least 2 cases, the most important being temperature.  This results in the Tuya integration reporting a random (usually negative) false value for current temp. The other problem is it sends its temp values as degrees F and ALL esphome climate entities originate in C.  If you set your HA instance to imperial, it will automagically convert C to F.  In this case it convering what it thinks is C ( but is really F) into F again.  temp readings are whacked and there was nothing you can do until now.

link to product manual https://www.cleveland-ironworks.com/mwdownloads/download/link/id/2763

Their app is a vendor written Tuya based app that looks like this:

![image](https://user-images.githubusercontent.com/52110065/201826389-4d6983e2-d4e9-4c8c-8e9a-fdad121f7824.png)


![image](https://user-images.githubusercontent.com/52110065/201826977-369853d6-650e-4048-9e9a-6701e3d1621c.png)

So, the main problems with trying to control it manually are setting your target temp doesn't work bc it fights with my stove's internal "set temp" that is set thru the front panel. when the room temp sensor reaches the user set value it shuts off to stove - a self contained system. there is no manual way to get around it and convert it to a manual operation. too many sensors, blowers, igniters, relays and safety issues to etc to deal with.

**Solution**
- Flash ESPHome to the chip using TuyaMCU
- use the new mod I got one of the ESPhome devs to make for me and you're golden.  its defined in the esphome config file.
- if your stove is turning off for no reason w/ "Goodbye" displayed on the screen, then the automations I'm working on should help mitigate this

See the PR's for specific solutions to some of the errors and problems I've solved over the past year.

Have fun.

**Data Points:**
```
P1 - Power on (Heat)
4 - Mode P1/P2/P3P4
101 - ECO1/ECO2
104 - Error Code
106 Set Temp
107 - Current Teemp
108 - Pipe Temp
109 - Protect Temp
```
Error code - 104 (these come back from the server as numbers and are then mapped to error codes in the vendor app)

Flashing the chip
Remove it from the display module.  It unplugs easily.
![image](https://user-images.githubusercontent.com/52110065/201829197-9dbe42c8-2a3b-4ed6-bd42-652bc7af61cb.png)
![image](https://user-images.githubusercontent.com/52110065/201829293-01f14b40-6578-4f13-be3f-9fe1ad663b63.png)

this link shows you how to do it: https://tasmota.github.io/docs/TuyaMCU-Devices/#costco-charging-essentials

EDIT: for future reference, I only grounded GPIO0, grounding RST wouldn't let me flash the chip.
WARNING - be careful when you solder wires to the board/chip to flash the chip.  I used breadbord wires w/pins and my VCC conneection broke and it took most of the circuit board trace off both the board AND the chip.  I salvaged it with a Frankenstein jumper, but you've been warned!

![image](https://user-images.githubusercontent.com/52110065/201826705-5dca2316-681d-4a11-b2fe-dcdd6da0d05e.png)

The spiffy new entity with options to change Power and ECO mode.

![Screenshot from 2022-11-15 14-29-39](https://user-images.githubusercontent.com/52110065/202032861-c4ea4b0f-2f69-43af-9834-0432102438a4.png)





