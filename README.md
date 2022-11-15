**Product Model:** Cleveland Ironworks Wood Pellet Stove (there are 4 models, all use the same controller).  
I have a test bench set up with a spare control board.

It also appears from the Wifi module (N12210) that this exact same controller is used in Nemaxx Pellet Stove Pellet Heater P6 P9 P12.  https://www.ebay.com/itm/193755684864

link to product manual https://www.cleveland-ironworks.com/mwdownloads/download/link/id/2763

Their app is a Tuya based app tht looks like this:

![image](https://user-images.githubusercontent.com/52110065/201826389-4d6983e2-d4e9-4c8c-8e9a-fdad121f7824.png)

It works ok, but the stove malfunctions fairly frequently.  This is an attempt to mitigate all that.

Pellet stoves made by Cleveland Ironworks all use the TuyaMCU chip TYWE1S to communicate with the stove's MCU inside the display unit.  Their shoddy programmer defined multiple datapoints for the same attribute in at least 2 cases, the most important being temperature.    The other problem is it sends its temp values as degrees F and ALL esphome climate entities originate in C.  If you set your HA instance to imperial, it will automagically convert C to F.  In this case it convering what it thinks is C ( but is really F) into F again.  temp readings are whacked and there was nothing you can do until now.

- Flash ESPHome to the chip.
- use the new mod I got one of he ESPhome devs to make for me and you're golden.
- if your stove is turning off for no reason w/ "Goodbye" displayed on the screen, then the automations I'm working on should help mitigate that.

Have fun.

**Data Points:**
P1 - Power on (Heat)
4 - Mode P1/P2/P3P4
101 - ECO1/ECO2
104 - Error Code
106 Set Temp
107 - Current Teemp
108 - Pipe Temp
109 - Protect Temp

Error code - 104 (these come back from the server as numbers and are then mapped to error codes in the vendor app)

Flashing the chip

![image](https://user-images.githubusercontent.com/52110065/201826705-5dca2316-681d-4a11-b2fe-dcdd6da0d05e.png)

this link shows you how to do it: https://tasmota.github.io/docs/TuyaMCU-Devices/#costco-charging-essentials


**Data Points:**
