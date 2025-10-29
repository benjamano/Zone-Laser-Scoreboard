import time
import os
import subprocess
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv("../.env")

# Import functions from networkinterfaces.py
try:
    import networkUtils as net
except ImportError as e:
    print(f"Failed to import networkinterfaces: {e}")
    input("Press Enter to exit")
    sys.exit(1)

# print("Web App Status Checker Started, hiding console")
# ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

TRIES_BEFORE_RESTART = 3
TRIES_BEFORE_REBOOT = 12
CHECK_INTERVAL = 60  # seconds

tries = 0

while True:
    try:
        # Use adapter-specific IP if possible
        try:
            ip = net.get_ip_by_adapter(os.getenv("PREFERRED_NETWORK_INTERFACE", ""))
            if ip == "":
                ip = net.get_local_ip()
        except Exception:
            # fallback if adapter not found or fails
            ip = net.get_local_ip()

        dir = os.path.dirname(os.path.realpath(__file__))

        print(f"Checking server status at {ip} with directory {dir}")

        try:
            response = requests.get(f"http://{ip}:8080/ping", timeout=5)
            status_code = response.status_code
        except Exception as e:
            print(f"Failed to ping server: {e}")
            status_code = 500

        if status_code == 200:
            tries = 0
        else:
            tries += 1
            print(f"Ping failed ({tries} consecutive failures).")

            if tries == TRIES_BEFORE_RESTART:
                print("Attempting to restart server...")
                subprocess.Popen(
                    [f"runPython.bat"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

            elif tries > TRIES_BEFORE_REBOOT:
                print("Too many failures, rebooting system.")
                os.system("shutdown /r /t 1")
                tries = 0

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"Failed to check server status: {e}")
        time.sleep(CHECK_INTERVAL)