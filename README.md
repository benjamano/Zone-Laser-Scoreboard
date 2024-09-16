# Zone Laser Tag Scoreboard / Packet Sniffer

This system uses python to sniff the network for packets that are coming from or going to the Zone Laser control box.

So far, it can only detect the start and the end of games. I'm currently working on the detection of hits / scores.

I want this system to be able to store historical records of games, allowing for player's real names to be inserted.
I also want Player data to be deleted after 2 yeas of inactivity, to save on storage & GDPR regulations.

## Packets decoded so far:

Values are seperated by commas by the control box.

| Packet Name       | Hex Bytes       | ASCII Conversion | Details     |
| :---------------- | :------:        | :------          |:------      |
| Game Start        |  342c403031352c30    | 4,@015,0      | "4" - Game Mode, "@015" - Game Status, "0" - Unknown  |
| Game End          |  342c403031342c30    | 4,@014,0      | "4" - Game Mode, "@015" - Game Status, "0" - Unknown |
| Timing            |  coming soon    | coming soon      | coming soon |
| Shot Made         |  coming soon    | coming soon      | coming soon |
| Shot Confirmed    |  coming soon    | coming soon      | coming soon |

## Code / File Breakdown
