import datetime
import logging
import requests
import socket
import os
import threading
import queue
from dotenv import dotenv_values

reset = "\033[0m"
colours = {
    "Info": "\033[94m",
    "Warning": "\033[93m",
    "Error": "\033[91m",
    "Success": "\033[92m",
    "Red": "\033[31m",
    "Green": "\033[32m",
    "Yellow": "\033[33m",
    "Blue": "\033[34m",
    "Magenta": "\033[35m",
    "Cyan": "\033[36m",
    "Black": "\033[30m"
}

secrets = dotenv_values(".env")

class Format:
    def __init__(self, ServiceName=""):
        self.serviceName = ServiceName
        self.logger = logging.getLogger("webAppLogger")
        self._localIp = ""
        self.queue = queue.Queue()
        self._startLogThread()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            self.queue.put(("Error", f"Error finding local IP: {e}", True, False))

    def _startLogThread(self):
        thread = threading.Thread(target=self._logWorker, daemon=True)
        thread.start()

    def _logWorker(self):
        while True:
            log_type, message, date, newline = self.queue.get()
            try:
                self._processLogMessage(message, log_type, date, newline)
            except Exception as e:
                print(f"Log processor exploded: {e}")
            self.queue.task_done()

    def message(self, message, type="Info", date=True, newline=False):
        self.queue.put((type.title(), message, date, newline))

    def _processLogMessage(self, message, type="Info", date=True, newline=False):
        logtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = colours.get(type, "\033[94m")
        parts = []

        if newline:
            parts.append("")

        if date:
            parts.append(logtime)

        serviceWidth = 10
        if self.serviceName:
            padded_service = f"{self.serviceName:<{serviceWidth}}"
            parts.append(padded_service)
        else:
            parts.append(" " * serviceWidth)

        parts.append(type)

        formatted = " | ".join(parts)
        formatted = f"{color}{formatted}{reset} : {message}"

        print(formatted, flush=True)

        log_text = f"{logtime} | {self.serviceName} | {type} | {message}"

        try:
            if type == "Error":
                self.logger.error(log_text)
                self.sendEmail(message, type)
            elif type == "Warning":
                self.logger.warning(log_text)
            else:
                self.logger.info(log_text)

            if "dev" not in secrets["Environment"].lower():
                try:
                    requests.post(
                        f'http://{self._localIp}:8080/sendMessage',
                        json={"message": {"message": message, "logType": type}, "type": "logMessage"}
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"Error sending log message: {e}, MESSAGE: {message}")

    def newline(self, withDivider=True, baronly=False):
        if baronly:
            print("\t\t    |")
        elif withDivider:
            print("-" * 20 + "+" + "-" * 90)
        else:
            print("-" * 111)

    def colourText(self, text: str, colour: str):
        return f"{colours.get(colour.title(), '\033[94m')}{text}{reset}"

    def sendEmail(self, content, type):
        try:
            if "dev" in secrets["Environment"].lower():
                return

            url = "https://benmercer.pythonanywhere.com/play2day/api/sendLogMessage"
            data = {
                "type": type.title(),
                "messegeContent": content + f"<br>Sent by Environment: {secrets['Environment']}",
                "secretKey": secrets["EmailSecretKey"],
            }

            requests.post(url, data=data)
        except Exception as e:
            self.queue.put(("Warning", f"Failed to send log message to server: {e}", True, False))
            