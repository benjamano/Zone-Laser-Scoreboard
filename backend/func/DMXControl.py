import os, json
from os import walk
from PyDMXControl.controllers import OpenDMXController
from PyDMXControl.profiles.Generic import Custom, Dimmer
            
from func import format
            
class dmx:
    def __init__(self):
        self._dmx = OpenDMXController()         

        self.fixtures = {}
        self.scenes = {}
        self.fixtureGroups = {}
        self.fixtureProfiles = {
                "Dimmer": {
                    "Dimmer": list(range(0, 255)),
                },
                "Colorspot575XT": {
                    "Pan": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "PanTilt Speed": {},
                    "FanLamp Control": {},
                    "Colour 1": {
                    "White": 0,
                    "Light blue": 13,
                    "Red": 26,
                    "Blue": 38,
                    "Light green": 51,
                    "Yellow": 64,
                    "Magenta": 77,
                    "Cyan": 90,
                    "Green": 102,
                    "Orange": 115,
                    "Rainbow": list(range(128, 255)),
                    },
                    "Colour 2": {
                    "White": 0,
                    "Deep Red": 12,
                    "Deep Blue": 24,
                    "Pink": 36,
                    "Cyan": 48,
                    "Magenta": 60,
                    "Yellow": 72,
                    "5600K Filter": 84,
                    "3200K Filter": 96,
                    "UV": 108
                    },
                    "Prism": {
                    "Open": 0,
                    "Rotation": list(range(1, 127)),
                    },
                    "Macros": {},
                    "Gobos": {
                    "Open": list(range(0, 7)),
                    "1": list(range(8, 15)), 
                    "2": list(range(16, 23)), 
                    "3": list(range(24, 31)), 
                    "4": list(range(32, 39)), 
                    "5": list(range(40, 47)), 
                    "6": list(range(48, 55)), 
                    "7": list(range(56, 63)), 
                    "8": list(range(64, 71)), 
                    "9": list(range(72, 79)), 
                    "1 Shaking": list(range(80, 95)), 
                    "2 Shaking": list(range(96, 111)), 
                    "3 Shaking": list(range(112, 127)), 
                    "4 Shaking": list(range(128, 143)), 
                    "5 Shaking": list(range(144, 159)), 
                    "6 Shaking": list(range(160, 175)), 
                    "7 Shaking": list(range(176, 191)), 
                    "8 Shaking": list(range(192, 207)), 
                    "9 Shaking": list(range(208, 223)), 
                    "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotating Gobos": {    
                    "Open": list(range(0, 31)),
                    "1": list(range(32, 63)), 
                    "2": list(range(64, 95)), 
                    "3": list(range(96, 127)), 
                    "4": list(range(128, 159)), 
                    "5": list(range(160, 191)), 
                    "6": list(range(192, 223)), 
                    "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotation Speed": {
                    "Indexing": list(range(0, 127)),    
                    "Rotation": list(range(128, 255)),    
                    },
                    "Iris": {
                    "Open": 0,
                    "MaxToMin": list(range(1, 179)),   
                    "Closed": list(range(180, 191)),   
                    "Pulse Close Slow Fast": list(range(192, 223)),   
                    "Pulse Open Fast Slow": list(range(224, 225)),   
                    },
                    "Focus": list(range(0, 255)),
                    "Strobe / Shutter": {
                    "Closed": list(range(0, 32)),   
                    "Open": list(range(32, 63)),   
                    "Strobe Slow Fast": list(range(64, 95)),   
                    "Pulse Slow Fast": list(range(128, 159)),   
                    "Random Slow Fast": list(range(192, 223)),   
                    },
                    "Dimmer": list(range(0, 255)),
                },
                "Colorspot250AT": {
                    "Pan": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "Pan Tilt Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special Functions": {},
                    "Pan Tilt Macros": {},
                    "Pan Tilt Macros Speed": {},
                    "Colour 1": {
                    "White": 0,
                    "Dark green": 11,
                    "Red": 23,
                    "Light azure": 34,
                    "Magenta": 46,
                    "UV filter": 58,
                    "Yellow": 70,
                    "Green": 81,
                    "Pink": 93,
                    "Blue": 105,
                    "Deep red": 117,
                    "Rotation": list(range(190, 243)),
                    "Audio": list(range(224, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": list(range(0, 255)),
                    "Gobos": {
                    "Open": list(range(0, 3)),
                    "1": list(range(4, 7)),   
                    "2": list(range(8, 11)),   
                    "3": list(range(12, 15)),   
                    "4": list(range(16, 19)),   
                    "5": list(range(20, 23)),   
                    "6": list(range(24, 27)),   
                    "7": list(range(28, 31)),   
                    "1 Rotating": list(range(32, 35)),
                    "2 Rotating": list(range(36, 39)),
                    "3 Rotating": list(range(40, 43)),
                    "4 Rotating": list(range(44, 47)),
                    "5 Rotating": list(range(48, 51)),
                    "6 Rotating": list(range(52, 55)),
                    "7 Rotating": list(range(56, 59)),
                    "1 Shaking Slow Fast": list(range(60, 69)),
                    "2 Shaking Slow Fast": list(range(70, 79)),
                    "3 Shaking Slow Fast": list(range(80, 89)),
                    "4 Shaking Slow Fast": list(range(90, 99)),
                    "5 Shaking Slow Fast": list(range(100, 109)),
                    "6 Shaking Slow Fast": list(range(110, 119)),
                    "7 Shaking Slow Fast": list(range(120, 139)),
                    "1 Shaking Fast Slow": list(range(130, 139)),
                    "2 Shaking Fast Slow": list(range(140, 149)),
                    "3 Shaking Fast Slow": list(range(150, 159)),
                    "4 Shaking Fast Slow": list(range(160, 169)),
                    "5 Shaking Fast Slow": list(range(170, 179)),
                    "6 Shaking Fast Slow": list(range(180, 189)),
                    "7 Shaking Fast Slow": list(range(190, 199)),
                    "Rotation": list(range(202, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Gobo Rotation Speed": {
                    "No Rotation": 0,
                    "Rotation": list(range(1, 255)),  
                    },
                    "Gobo Fine Position": list(range(0, 255)),
                    "Prism": {
                    "Open position (hole)": list(range(0, 19)),
                    "3-facet": list(range(20, 159)),
                    "Macro 1": list(range(160, 167)),
                    "Macro 2": list(range(168, 175)),
                    "Macro 3": list(range(176, 183)),
                    "Macro 4": list(range(184, 191)),
                    "Macro 5": list(range(192, 199)),
                    "Macro 6": list(range(200, 207)),
                    "Macro 7": list(range(208, 215)),
                    "Macro 8": list(range(216, 223)),
                    "Macro 9": list(range(224, 231)),
                    "Macro 10": list(range(232, 239)),
                    "Macro 11": list(range(240, 247)),
                    "Macro 12": list(range(248, 255)),
                    },
                    "Prism Rotation": {
                    "No Rotation": 0,
                    "Rotation": list(range(1, 255)), 
                    },
                    "Focus": list(range(1, 255)),
                    "Focus Fine": list(range(1, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe Slow Fast": list(range(64, 95)),
                    "Pulse Slow Fast": list(range(128, 143)),
                    "Pulse Fast Slow": list(range(144, 159)),
                    "Random Slow Fast": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer Fine": list(range(0, 255)),
                },
                "Colorwash250AT": {
                    "Pan": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "Pan Tilt Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special Functions": {},
                    "Pan Tilt Macros": {},
                    "Pan Tilt Macros Speed": {},
                    "Colour 1": {
                    "White": 0,
                    "Red": 18,
                    "Blue": 36,
                    "Green": 54,
                    "3200K Filter": 72,
                    "6000K Filter": 90,
                    "UV": list(range(190, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": list(range(0, 255)),
                    "Cyan": list(range(0, 255)),
                    "Magenta": list(range(0, 255)),
                    "Yellow": list(range(0, 255)),
                    "CMY Dimmer Speed": list(range(0, 255)),
                    "CMY Macros": {
                    "Open": list(range(0, 7)),
                    "Rainbow Fast Slow": list(range(240, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Effect Wheel": {
                    "Open": list(range(0, 70)),  
                    "Beam Shaper": list(range(71, 179)),  
                    "Swivelling Slow Fast": list(range(180, 199)),  
                    "Frost": list(range(200, 255)),  
                    },
                    "Zoom": list(range(0, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe Slow Fast": list(range(64, 95)),
                    "Opening Pulse Slow Fast": list(range(128, 143)),
                    "Closing Pulse Fast Slow": list(range(144, 159)),
                    "Random": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer Fine": list(range(0, 255)),
                }
            }
    
        try:
            self.scenes = self.getScenesFromFileSystem()
        except Exception as e:
            format.message(f"Error processing DMX scenes: {e}", "error")
            
    # Setters
    
    def __appendToFixtures(self, fixture, fixtureType):
        self.fixtures[fixture.name] = {"type": fixtureType, "id": fixture.id}

    def addFixtureToGroup(self, groupName, fixture):
        if groupName not in self.fixtureGroups:
            self.fixtureGroups[groupName] = []
            
        self.fixtureGroups[groupName].append(fixture)
        
        return self.fixtureGroups[groupName]
        
    def registerDimmerFixture(self, fixtureName):
        try:
            fixture = self._dmx.add_fixture(Dimmer, name=fixtureName)
            setattr(self, fixtureName, fixture)
            
            self.__appendToFixtures(fixture, "Dimmer")
            
            return fixture
        except Exception as e:
            format.message(f"Error registering Dimmer fixture: {e}", "error")
            return None
    
    def registerCustomFixture(self, fixtureName, fixtureType, channels, startChannel):
        try:
            fixture = self._dmx.add_fixture(Custom(channels=channels, name=fixtureName, start_channel=startChannel))
            
            setattr(self, fixtureName, fixture)
        
            self.__appendToFixtures(fixture, fixtureType)
            
            return fixture
        except Exception as e:
            format.message(f"Error registering Custom fixture: {e}", "error")
            return None
        
    def registerFixtureUsingType(self, fixtureName, fixtureType, startChannel):
        try:
            if fixtureType in self._fixtureProfiles:
                fixture = self._dmx.add_fixture(Custom(channels=0, start_channel=startChannel, name=fixtureName))
                
                setattr(self, fixtureName, fixture)
                
                self.__appendToFixtures(fixture, fixtureType)
                
                for channel in self._fixtureProfiles[fixtureType]:
                    fixture._register_channel(channel)
                
                return fixture
            
            return LookupError
        except Exception as e:
            format.message(f"Error registering fixture: {e}", "error")
            return
        
    def registerChannel(self, fixtureName, channelName):
        try:
            fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture._register_channel(channelName)
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            format.message(f"Error registering channel: {e}", "error")
        
    def setFixtureChannel(self, fixtureName, channelName, value):
        try:
            fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture.set_channel(channelName.lower(), int(value))
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            format.message(f"Error setting channel: {e}", "error")
            
    # Getters
        
    def getFixtureProfiles(self):
        return self.fixtureProfiles
    def getFixtures(self):
        return self.fixtures
    def getFixtureTypes(self):
        return list(self._fixtureProfiles.keys())
    def getFixtureGroups(self):
        return self.fixtureGroups
    def getFixturesByName(self, fixtureName):
        return self._dmx.get_fixtures_by_name(fixtureName)
    def getDMXScenes(self):
        return self.getScenesFromFileSystem()
    def getScenesFromFileSystem(self):
        return self.processJSONDMXScenes(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data", "DMXScenes"))
    
    # Processing
    
    def processJSONDMXScenes(self, folder):
        scenes = {}
        
        for (dirpath, dirnames, filenames) in walk(folder):
            format.message(f"Processing {len(filenames)} DMX scenes", "info")
            
            for filename in filenames:
                if filename.endswith(".json"):
                    with open(folder+"\\"+filename) as json_file:
                        try:
                            scene = json.load(json_file)

                            scenes[str(filename).strip(".json")] = scene           
                        except Exception as e:
                            format.message(f"Error processing DMX scene {filename}: {e}", "error")
        
        return scenes
            
    # Config
    
    def enableWebInterface(self):
        try:
            self._dmx.web_control()
        except Exception as e:
            format.message(f"Error enabling web interface: {e}", "error")
        