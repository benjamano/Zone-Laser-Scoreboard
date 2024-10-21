# Zone Laser Tag Scoreboard / Packet Sniffer

**CURRENTLY THIS ONLY WORKS WITH THE BEGEARA 2 SYSTEM**

This system uses python to sniff the network for packets that are coming from or going to the Zone Laser control box.
It runs a simple Web App, run by Flask.
The app is designed for use inside of a Laser-Tag arena, allowing it to control the media on the computer it is running on.
It also attempts to setup a connection to the OBS Websocket extension, but the connection isn't used as of yet.
If the system cannot connect to OBS, it will still run.

# Pre-Requisites

For DMX to work, you must have a USB - DMX adaptor that support either Open DMX or UDMX. I use a cheap one off Amazon.
The DMX - USB MUST have the ```libusb-win32``` driver installed.
> NOTE: Installing this driver will cause QLC+ (And presumably others) to not recognise the adaptor anymore.
> This can be fixed by reinstalling the original driver on the adaptor, the original drivers will most likely be on the manufacturer's website.

For OBS to work, you MUST make a ```keys.txt``` file in the same directory as the scoreboard.py file.
Press enter 3 times in this file and then add your ```OBS Websocket IP```, ```OBS Websocket Password``` and the ```OBS Websocket Port```.
The program will read these and attempt to connect to the OBS Websocket instance.

All libraries should be installed when you run the ```Scoreboard.py``` file.

# Planned Feature Status

| Feature                                                               | Status                                             | Comments                                                                                                                        |
| :----------------                                                     | :------                                            | :------                                                                                                                         |
|Store Game Data in Database, Allow Player names to be added / looked up| Started                                            | DB is setup, saving to DB is not supported yet as the game doesn't keep track of scores in the backend just yet.                |
|DMX Lighting Control                                                   | Started                                            | A DMX connection is setup at runtime, but nothing is done yet as I have no way to test if it works (Will be able to soon)       |
|DMX Lighting Reacting to game events E.G. Game End / Start, Colour of the winning team, Colour change on BPM | Not Started  | Will get on with this once I can test it                                                                                        |
|Advanced music control                                                 | Almost Done                                        | Music starts when games ends, some bugs have shown up where it wont pause on game end, this is being looked into                |
|Randomly select lighting effects at game start for unique experience   | Not Started                                        | Some small bits for this - Basically not started as no way of testing yet.                                                      |
|Turn certain lights on when a target is shot                           | Not Started                                        | No way of testing and no hardware for target just yet, more of a longshot idea                                                  |
|Advanced OBS control                                                   | Started                                            | Allow for certains creens around the arena to change based on game status - So far it only creates a web-socket connection      |
|Track game progress / scores                                           | Almost Done                                        | Can detect game end, start, shot, individual player scores and timing packets. Left is shot confirmed and team scores           |
|Interactive web page that opens when the program starts                | Done                                               | Page works well, tracking player scores, song BPM / playing song details, game status but there are plans for some new things...|


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

## Code / File Breakdown

I'd like to imagine the code is easily decipherable, but if there are any question, email me @ benmercer76@btinternet.com

### Scoreboard.py

This is the "Main" code, it starts all the required processes up, It starts the Tkinter UI, that is mainly used for debugging and a small startup animation, the tray Icon, allowing for the Tkinter debug interface to be opened or the server to be closed.
When the Tkinter "ui" object is imported and run, the process for starting the WebApp begins, this is done by calling the "WebApp" object imported from the WebApp.py file after a countdown.

### \_\_init__.py

This file is called to import every function that is needed, if a required library isn't installed on the Host PC, it will download it automatically, which means no manual PIP work is required to use this.

### func/format.py

This is my replacement for the "print" statement, kinda, it just formats it all nicely and shows errors, warnings, info and successes in different colours, as well as aligning all entries in a very nice way.
It's pretty simple but it's probably my favourite part of this entire project, and I didn't even make it for this project!

### UserInterf.py

The User Interface code, should be easy to understand if you've used Tkinter before as it's a very simple library.
There's 2 views defined in this file, the startup view, and debugging view.

#### Startup View

This view has a simple progress bar, countdown and some text, just to show that the WebApp is starting, one day I might link the Progressbar to something other than a countdown as It's just theres for the looks really.

#### Debug View

This view as some debugging features that can be used for testing different parts of the app.
This view could go completely un used and make no effect on the system what-so-ever.

### WebApp.py

This is the actually cool bit, it does all the thinking, the doing and the breaking in this whole project.

This file starts by defining a class "WebApp" which is used by the "UserInterf.py" to call and start the Web App.
The first thing that happens is the ```__init__``` function is called, this will start defining all the variables that may be used, as well as initialise certain parts of the app.
Firstly, it defines the App, using Flask.

#### Variable Context:

__expectedProcesses = []__
The variable above determines what programs the script should expect to be running on the device. Every 5 minutes, the program checks if these processes are running, if not, it will open them. This is necesary as we use OBS and spotify for projection to the TVs around the Arena and music repsecitvely, and these must always be running, if they crash this script will now re-open them.

___dir__ = ""
This variable stores the directory the file is running in, making it easier to open files etc that will be in different directories depending on what PC it is running on.

I've skipped a few as I'd like to imagine they are easy to understand.

After the variables have been defined, it starts setting up the various processes.
Firstly, it called the setuplogging function, which is in the name, at the moment it does nothing as I have yet to implement anything.
Next, It starts a SocketIO connection for quick data transmission between the Web CLient and Host Web App.
Then it sets up all the routes to be used / available.
Next it attempts to open the files that store certain data inside of them that is either private or dependant on which system it is running on, so these are .gitignored.
It then initialises a DMX connection, a lighting protocol used for theatre lighting. This will soon be used to control lights inside of the arena. The program will start properly even if any of the above functions fail.
Then, it creates the Database and seeds it if necessary.

As the "start" function is called by the Tkinter UI, these instructions are carried out:

Attemptes to connect to OBS WebSocket, for advanced scene control that hasn't been used just yet.
Hides the python console window, this doesnt seem to work with Windows 11 anymore, but it does work on Windows 10.
Starts Packet Sniffing (See Packet Decoding Functions)
Starts the process checker as mentioned earlier.
Finds the local IP of the system, making routing easier, aswell as open a browser to the local IP.
Finally, the Web App is started, on the device's local, non-routable, network IP, to allow for internal devices to view the site too.

#### Packet Decoding Functions

When Packet Sniffing is begun, a callback function is selected, which is called everytime a packet is detected.
This Packet Callback function thread the function calls inside of it to greatly improve performance, seriously, it fell about 10 minutes behind one time without threading.
Firstly, it checks to see if the Source IP is coming from the expected area (The Zone Control Box), I'll make this easier to set, rather than it being hard coded later.
It then converts the packet data to a HEX format.
And then decodes this into an ASCII string useing a helpful function I stole from someone.
Then I split the value returned into a list as all the values are comma seperated.

Now here comes the exciting bit, it has to workout what type of packet it is handling, this is done by looking at the first bit of the list, which is always the Event Type in the packet.
Most of the comments and names here shoudld explain the rest, if you run into any problems, please raise an issue or email me @ benmercer76@btinternet.com

Thanks for reading.
