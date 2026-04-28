"""
BMS Blood Stock - Launcher
Wraps the Node.js server with a Tkinter GUI for easy startup
Build to .exe with PyInstaller (see build_exe.bat)
"""
import os
import sys
import subprocess
import threading
import webbrowser
import shutil
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

APP_NAME = "BMS Blood Stock"
PORT = 7712
URL = f"http://localhost:{PORT}"


def app_dir():
    """Return directory containing server.js
    Searches: .exe/script dir → parent dir → grandparent dir
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    # Walk up to 3 levels looking for server.js
    candidate = base
    for _ in range(3):
        if os.path.isfile(os.path.join(candidate, "server.js")):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    # Fallback to .exe directory
    return base


def find_node():
    """Find node.exe in PATH or common locations"""
    node = shutil.which("node")
    if node:
        return node
    common = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.join(os.environ.get("APPDATA", ""), "npm", "node.exe"),
    ]
    for p in common:
        if os.path.isfile(p):
            return p
    return None


def find_npm():
    """Find npm executable"""
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm:
        return npm
    common = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
    ]
    for p in common:
        if os.path.isfile(p):
            return p
    return None


class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.stop_log_thread = False
        self.app_dir = app_dir()

        root.title(f"{APP_NAME} Launcher")
        root.geometry("720x500")
        root.minsize(600, 400)
        try:
            root.iconbitmap(default="")
        except Exception:
            pass

        # Header
        header = tk.Frame(root, bg="#450a0a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"🩸 {APP_NAME}",
                 bg="#450a0a", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=20)
        self.status_var = tk.StringVar(value="● Stopped")
        self.status_label = tk.Label(header, textvariable=self.status_var,
                                     bg="#450a0a", fg="#f87171",
                                     font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", padx=20)

        # Info bar
        info = tk.Frame(root, bg="#f3f4f6")
        info.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(info, text=f"URL: {URL}",
                 bg="#f3f4f6", fg="#374151",
                 font=("Consolas", 10)).pack(side="left", padx=8, pady=6)
        tk.Label(info, text=f"Port: {PORT}",
                 bg="#f3f4f6", fg="#6b7280",
                 font=("Consolas", 10)).pack(side="left", padx=8, pady=6)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=12, pady=4)
        self.start_btn = tk.Button(btn_frame, text="▶ Start Server",
                                   command=self.start_server,
                                   bg="#059669", fg="white",
                                   font=("Segoe UI", 10, "bold"),
                                   padx=14, pady=6, bd=0,
                                   activebackground="#047857",
                                   activeforeground="white",
                                   cursor="hand2")
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = tk.Button(btn_frame, text="■ Stop Server",
                                  command=self.stop_server,
                                  bg="#dc2626", fg="white",
                                  font=("Segoe UI", 10, "bold"),
                                  padx=14, pady=6, bd=0,
                                  activebackground="#b91c1c",
                                  activeforeground="white",
                                  cursor="hand2",
                                  state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.browser_btn = tk.Button(btn_frame, text="🌐 Open Dashboard",
                                     command=self.open_browser,
                                     bg="#2563eb", fg="white",
                                     font=("Segoe UI", 10, "bold"),
                                     padx=14, pady=6, bd=0,
                                     activebackground="#1d4ed8",
                                     activeforeground="white",
                                     cursor="hand2",
                                     state="disabled")
        self.browser_btn.pack(side="left", padx=4)

        tk.Button(btn_frame, text="⚙ Open Folder",
                  command=lambda: os.startfile(self.app_dir),
                  bg="#6b7280", fg="white",
                  font=("Segoe UI", 10, "bold"),
                  padx=14, pady=6, bd=0,
                  cursor="hand2").pack(side="right", padx=4)

        # Log
        log_label = tk.Label(root, text="📋 Server Log:",
                             font=("Segoe UI", 9, "bold"), anchor="w")
        log_label.pack(fill="x", padx=12, pady=(8, 2))

        self.log = scrolledtext.ScrolledText(root, height=18,
                                             font=("Consolas", 9),
                                             bg="#1e293b", fg="#e2e8f0",
                                             insertbackground="white",
                                             wrap="word")
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log.tag_configure("err", foreground="#fca5a5")
        self.log.tag_configure("ok", foreground="#86efac")
        self.log.tag_configure("info", foreground="#93c5fd")

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Auto-start
        self.append_log(f"App directory: {self.app_dir}", "info")
        self.start_server()

    def append_log(self, text, tag=None):
        self.log.insert("end", text + "\n", tag or "")
        self.log.see("end")

    def set_status(self, running):
        if running:
            self.status_var.set("● Running")
            self.status_label.config(fg="#86efac")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.browser_btn.config(state="normal")
        else:
            self.status_var.set("● Stopped")
            self.status_label.config(fg="#f87171")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.browser_btn.config(state="disabled")

    def ensure_dependencies(self):
        """Run npm install if node_modules missing"""
        nm = os.path.join(self.app_dir, "node_modules")
        if os.path.isdir(nm):
            return True
        npm = find_npm()
        if not npm:
            self.append_log("ERROR: npm not found. Please install Node.js from https://nodejs.org", "err")
            return False
        self.append_log("Installing dependencies (first time only, please wait)...", "info")
        try:
            result = subprocess.run([npm, "install"],
                                    cwd=self.app_dir,
                                    capture_output=True, text=True,
                                    timeout=300,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if result.returncode == 0:
                self.append_log("Dependencies installed.", "ok")
                return True
            self.append_log(f"npm install failed:\n{result.stderr}", "err")
            return False
        except Exception as e:
            self.append_log(f"npm install error: {e}", "err")
            return False

    def start_server(self):
        if self.process and self.process.poll() is None:
            return

        node = find_node()
        if not node:
            self.append_log("ERROR: Node.js not found. Please install from https://nodejs.org", "err")
            messagebox.showerror("Node.js not found",
                                 "Please install Node.js from https://nodejs.org and try again.")
            return

        server_js = os.path.join(self.app_dir, "server.js")
        if not os.path.isfile(server_js):
            self.append_log(f"ERROR: server.js not found in {self.app_dir}", "err")
            messagebox.showerror("Missing file",
                                 f"server.js not found in:\n{self.app_dir}")
            return

        if not self.ensure_dependencies():
            return

        self.append_log(f"Starting Node.js server... (node {node})", "info")
        try:
            kwargs = {
                "cwd": self.app_dir,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "bufsize": 1,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self.process = subprocess.Popen([node, "server.js"], **kwargs)
        except Exception as e:
            self.append_log(f"Failed to start: {e}", "err")
            return

        self.set_status(True)
        self.stop_log_thread = False
        threading.Thread(target=self._read_log, daemon=True).start()

        # Auto-open browser after 2 seconds
        self.root.after(2000, self.open_browser)

    def _read_log(self):
        if not self.process or not self.process.stdout:
            return
        for line in iter(self.process.stdout.readline, ""):
            if self.stop_log_thread:
                break
            line = line.rstrip()
            if not line:
                continue
            tag = None
            low = line.lower()
            if "error" in low or "fail" in low:
                tag = "err"
            elif "listening" in low or "default db" in low or "✓" in line:
                tag = "ok"
            elif "[query]" in low or "dashboard" in low or "==" in line:
                tag = "info"
            self.root.after(0, self.append_log, line, tag)

        # Process exited
        rc = self.process.poll() if self.process else -1
        self.root.after(0, self.append_log, f"Server stopped (exit code: {rc})", "err")
        self.root.after(0, self.set_status, False)

    def stop_server(self):
        if not self.process:
            return
        self.stop_log_thread = True
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                               capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        except Exception as e:
            self.append_log(f"Stop error: {e}", "err")
        self.process = None
        self.set_status(False)
        self.append_log("Server stopped.", "info")

    def open_browser(self):
        webbrowser.open(URL)
        self.append_log(f"Opened {URL}", "info")

    def on_close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno("Stop server?",
                                       "Server is running. Stop and exit?"):
                return
            self.stop_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    LauncherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
