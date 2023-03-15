import datetime
import socket
import sys
import os

print("very")
print("DEBUG - " + str(datetime.datetime.now()) + " On system: " + socket.gethostname() + " On OS: " + sys.platform + " From file: " + os.path.dirname(os.path.abspath(__file__)))
