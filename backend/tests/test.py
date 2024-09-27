from PyDMXControl.controllers import OpenDMXController
# from PyDMXControl.controllers import uDMXController

# Import the fixture profile we will use,
#  the simple Dimmer in this example.
from PyDMXControl.profiles.Generic import Dimmer

# Create an instance of the uDMX controller, 
#  this holds all the fixture information and outputs it.
# This will start outputting data immediately.
dmx = OpenDMXController()