# Zone Laser Tag Scoreboard / Packet Sniffer

**CURRENTLY THIS ONLY WORKS WITH THE BEGEARA 2 SYSTEM**

This system uses python to sniff the network for packets that are coming from or going to the Zone Laser control box.

So far, it can only detect the start and the end of games. I'm currently working on the detection of hits / scores.

I want this system to be able to store historical records of games, allowing for player's real names to be inserted.
I also want Player data to be deleted after 2 yeas of inactivity, to save on storage & GDPR regulations.

## Packets decoded so far:

Values are seperated by commas by the control box.

| Packet Name       | Hex Bytes       | ASCII Conversion | Details     |
| :---------------- | :------:        | :------          |:------      |
| Game Start        |  342c403031352c30    | 4,@015,0      | "4" - Game Mode, "@015" - Game Status, "0" - Unknown  |
| Game End          |  342c403031342c30    | 4,@014,0      | "4" - Game Mode, "@014" - Game Status, "0" - Unknown |
| Timing            |  coming soon    | coming soon      | coming soon |
| Shot Made         |  coming soon    | coming soon      | coming soon |
| Shot Confirmed    |  coming soon    | coming soon      | coming soon |
| End of Game Scores|  coming soon    | coming soon      | coming soon |

# Scoreboard Set Up

# Extra Details

## Setup Zone Packet Sniffing

This is an annoying process.
You must be able to connect to the Begeara 2's local network. I have done it by using a simple ethernet cable connected to the network switch that connects the Android Display Controller and the actual control box.

After you've done that, I'd reccomend opening up "WireShark" a tool used for sniffing packets travelling along a network.
If you don't know the IP of either the Android or control box, I'd reccomend seting the filter to look for the domain of "Begeara.com", and restart the Zone system. 

The Zone system will call the "Begeara.com" URL everytime it starts to verify it's authenticity and license. 
When this packet shows, note down the "src" IP address. (This is the control box's IP)

Set a filter on wireshark to find packets coming from that IP, and you should be able to see the box communicating over the network!

## Code / File Breakdown
