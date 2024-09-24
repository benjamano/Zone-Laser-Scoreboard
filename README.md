# Zone Laser Tag Scoreboard / Packet Sniffer

**CURRENTLY THIS ONLY WORKS WITH THE BEGEARA 2 SYSTEM**

This system uses python to sniff the network for packets that are coming from or going to the Zone Laser control box.
It runs a simple Web App, run by Flask.
The app is designed for use inside of a Laser-Tag arena, allowing it to control the media on the computer it is running on.
It also attempts to setup a connection to the OBS Websocket extension, but the connection isn't used as of yet.
If the system cannot connect to OBS, it will still run.

So far, it can only detect the start and the end of games. I'm currently working on the detection of hits / score logging.

I want this system to be able to store historical records of games, allowing for player's real names to be inserted.
I also want Player data to be deleted after 2 years of inactivity, to save on storage & GDPR regulations.

## Packets decoded so far:
This table includes all the packets that I have currently decoded, I couldn't work out what some values are used for, thus the "?".
These should work exactly the same across all Begeara 2 Zone Laser systems.

Please view my webApp.py file to view the functions that I used to decode and process the data inside these packets.

Values are seperated by commas by the control box.

| Packet Type - Packet Name               | Hex Bytes                                          | ASCII Conversion           | Details                                                          | English Translation                                                      |
| :----------------                       | :------                                            | :------                    |:------                                                           |:------                                                                   | 
| 1 <br />Timing                          |  312c373537332c22403<br />03034222c3630302c31      | 1,7573,"@004",600,1        | EventType, Game Number, Game Mode?, Seconds Remaining, ?         | Game number 7573 (Game Mode Id 4) has 10 Minutes (600 Seconds) remaining |
| 2 * <br />Team Scores                   |  coming soon                                       | coming soon                | EventType, coming soon                                           | coming soon                                                              |
| 3 * <br />End of Game Scores            |  332c312c302c33302c31<br />2c33302c332c31302c30    | 3,1,0,30,1,30,3,10,0       | EventType, GunID, Team, Score, Rank, Accuracy, Shots Fired, ?, ? | Gun Id 1, Team 1, has a final score of 30 and a final acurracy of 30%    |
| 4 <br />Game Start                      |  342c403031352c30                                  | 4,@015,0                   | EventType, Game Status, ?                                        | The Game Started                                                         | 
| 4 <br />Game End                        |  342c403031342c30                                  | 4,@014,0                   | EventType, Game Status, ?                                        | The Game Ended                                                           |
| 5 <br />Shot Confirmed                  |  352c31312c312c32<br />2c302c302c302c30            | 5,11,1,2,0,0,0,0           | EventType, GunShotId, ShooterGunId, ?, ?, ?, ?, ?                | Gun Id 11 was shot by Gun Id 1                                           |

* Packets represent teams using a Team Id. Red Team is Id 0 and Green is Id 2 for some reason. *

#### * Special Thanks to iR377 on Reddit, who helped me with identifying a few of the packets in the table above.

# Scoreboard Set Up

# Extra Details

## Setup Zone Packet Sniffing

This is an annoying process.
For this to work, you must connect to the Begeara 2's local network. I have done it by using a simple ethernet cable connected to the network switch that connects the Android Display Controller and the actual control box.

After you've done that, I'd recommend opening up "WireShark" a tool used for sniffing packets travelling along a network.
If you don't know the IP of either the Android or control box, I'd recommend setting the filter to look for the domain of "Begeara.com", and restart the Zone system. 

The Zone system will call the "Begeara.com" URL everytime it starts to verify it's authenticity and license. 
When this packet shows, note down the Source IP address. (This is the control box's IP)

Set a filter on wireshark to find packets coming from that IP, and you should be able to see the box communicating over the network!

## Code / File Breakdown
