# Zone Laser Tag Scoreboard / Packet Sniffer

**CURRENTLY THIS ONLY WORKS WITH THE BEGEARA 2 SYSTEM**

This system uses python to sniff the network for packets that are coming from or going to the Zone Laser control box.
It runs a simple Web App, run by Flask.
The app is designed for use inside of a Laser-Tag arena, allowing it to control the media on the computer it is running on.
It also attempts to setup a connection to the OBS Websocket extension,
If the system cannot connect to OBS, it will still run. The OBS Connection is used for more bespoke purposes in this software, for example, changing the outside screens to a "Sleep Mode" to reduce the burn in affect on the screens.
It will also try to connect to a DMX controller for various lighting effects, but it is also not required.

# Pre-Requisites

For DMX to work, you must have a USB - DMX adaptor that support either Open DMX or UDMX. I use a cheap one off Amazon.
The DMX - USB MUST have the ```libusb-win32``` driver installed.
> NOTE: Installing this driver will cause QLC+ (And presumably others) to not recognise the adaptor anymore.
> This can be fixed by reinstalling the original driver on the adaptor, the original drivers will most likely be on the manufacturer's website.

NOTE: For this software, the ```Open-DMX``` standard is being used. It should be easy enough to change it to ```UDMX``` but this has not been implemented.

For OBS to work, you MUST make a ```.env``` file in the same directory as the scoreboard.py file.
Add your ```OBS Websocket IP```, ```OBS Websocket Password``` and the ```OBS Websocket Port```.
The program will read these and attempt to connect to the OBS Websocket instance.

All dependancies should be automatically installed when you run the ```Scoreboard.py``` file.

## Packets decoded so far:
This table includes all the packets that I have currently decoded, I couldn't work out what some values are used for, thus the "?".
These should work exactly the same across all Begeara 2 Zone Laser systems.

Please view my webApp.py file to view the functions that I used to decode and process the data inside these packets.

Values are seperated by commas by the control box.

| Packet Type - Packet Name               | Hex Bytes                                          | ASCII Conversion           | Details                                                          | English Translation                                                      |
| :----------------                       | :------                                            | :------                    |:------                                                           |:------                                                                   | 
| 1 <br />Timing                          |  312c373537332c22403<br />03034222c3630302c31      | 1,7573,"@004",600,1        | EventType, Game Number, Game Mode?, Seconds Remaining, ?         | Game number 7573 (Game Mode Id 4) has 10 Minutes (600 Seconds) remaining |
| 2 * <br />Team Scores                   |  coming soon                                       | coming soon                | EventType, coming soon                                           | coming soon                                                              |
| 3 * <br />Player Scores                 |  332c312c302c33302c31<br />2c33302c332c31302c30    | 3,1,0,30,1,30,3,10,0       | EventType, GunID, Team, Score, Rank, ?, Shots Fired, Accuracy, ? | Gun Id 1, Team 1, has a score of 30 and an acurracy of 10%               |
| 4 <br />Game Start                      |  342c403031352c30                                  | 4,@015,0                   | EventType, Game Status, ?                                        | The Game Started                                                         | 
| 4 <br />Game End                        |  342c403031342c30                                  | 4,@014,0                   | EventType, Game Status, ?                                        | The Game Ended                                                           |
| 5 <br />Shot Confirmed                  |  352c31312c312c32<br />2c302c302c302c30            | 5,11,1,2,0,0,0,0           | EventType, GunShotId, ShooterGunId, ?, ?, ?, ?, ?                | Gun Id 11 was shot by Gun Id 1                                           |

> Teams are repsesented using a Team Id. Red Team is Id 0 and Green is Id 2 for some reason. *

#### * Special Thanks to iR377 on Reddit, who helped me with identifying a few of the packets in the table above.

# Scoreboard Set Up

# Extra Details

## Setup Zone Packet Sniffing

> You can use the ```networkInterfaces.py``` file to crosscheck which network adaptor you want to use. Use ```IPCONFIG``` on windows to find the IP / MAC address of the adaptor you want to use and compare it to the list given from the python file.

For this to work, you must connect to the Begeara 2's local network. I have done it by using a simple ethernet cable connected to the network switch that connects the Android Display Controller and the actual control box.

After you've done that, I'd recommend opening up "WireShark" a tool used for sniffing packets travelling along a network.
If you don't know the IP of either the Android or control box, I'd recommend setting the filter to look for the domain of "Begeara.com", and restart the Zone system. 

The Zone system will call the ```Begeara.com``` URL everytime it starts to verify it's authenticity and license. 
When this packet shows, note down the Source IP address. (This is the control box's IP)

Set a filter on wireshark to find packets coming from that IP, and you should be able to see the box communicating over the network!
