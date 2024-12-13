## DMX Integration

>The DMX integration into my this Python App has become quite complicated. I am considering making it's own Repo.

## This README is designed to explain the workings of dmx.py in the func folder.

### JSON Scene Storage

>Boy was this fun to make..

Scenes are stored in JSON files.
A Scene stores multiple objects:
- Overall Duration (Milliseconds)
- Repeat (Bool - Does the scene repeat after it finishes)
- Flash (Bool - Scene must be held down on the frontend to trigger it)
- Events (Array - Stores all each event in a scene)
- Events -->
  - Channels (Array - Stores the channel and value to be changed)
  - Durartion (Milliseconds - How long this event will last)

  #### Example JSON:

  ```
    {
        "name": "This Is A Test",
        "duration": 3000,
        "repeat": false,
        "flash": false,
        "events": {
            "1": {
                "channels": {
                    "ColorWash 250 AT": {
                        "Pan": 255,
                        "Tilt": 255
                    }
                },
                "duration": 1000
            },
            "2": {
                "channels": {
                    "ColorWash 250 AT": {
                        "Pan": 128,
                        "Tilt": 0
                    }
                },
                "duration": 1000
            },
            "3": {
                "channels": {
                    "ColorWash 250 AT": {
                        "Pan": 0,
                        "Tilt": 128
                    }
                },
                "duration": 1000
            }
        }
    }
