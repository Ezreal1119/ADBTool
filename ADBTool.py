#!/usr/bin/env python3
"""
@author: Patrick Xu (modified)
@date: 2025/08/10
@description: ADB Tool for Android devices using Python and Tkinter (macOS-friendly)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
from datetime import datetime
import shlex
import sys

# Optional: install ttkbootstrap for a modern theme:
# pip install ttkbootstrap
# import ttkbootstrap as tb

class ADBTool:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Tool (Patrick Xu) - macOS")
        self.adb_path = "/Users/patrickxu/Library/Android/sdk/platform-tools/adb"
        self.scrcpy_ath = "/Users/patrickxu/scrcpy-macos-aarch64-v3.3.1/scrcpy"
        # Start with a reasonable default size; user can resize
        self.root.geometry("1400x800")
        self.root.minsize(900, 600)

        # Optional modern theme with ttkbootstrap:
        # style = tb.Style(theme="litera")  # uncomment if using ttkbootstrap
        style = ttk.Style()
        # On macOS the default theme usually integrates well; set font defaults:
        default_font = ("Helvetica", 16)
        self.root.option_add("*Font", default_font)

        # Check if ADB is available
        if not self.check_adb():
            messagebox.showerror(
                "Error",
                "ADB not found. Please ensure Android SDK platform-tools installed and `adb` is on PATH.\n"
                "Install instructions: https://developer.android.com/studio/command-line/adb"
            )
            root.destroy()
            return

        # Top-level paned window: controls (top) and output (bottom)
        pw = ttk.Panedwindow(self.root, orient=tk.VERTICAL)
        pw.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        controls_frame = ttk.Frame(pw)
        output_frame = ttk.Frame(pw)

        pw.add(controls_frame, weight=9)
        pw.add(output_frame, weight=2)

        self.controls_frame = controls_frame
        self.output_frame = output_frame

        # Build controls (buttons + entries)
        self.create_controls()

        # Output text box with scrollbar
        self.output_text = tk.Text(self.output_frame, wrap="word", height=10)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,0), pady=(6,0))

        vsb = ttk.Scrollbar(self.output_frame, orient="vertical", command=self.output_text.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.configure(yscrollcommand=vsb.set)

        # Insert a short welcome message
        self.output_text.insert(tk.END, "ADB Tool ready. Click 'List Devices' to begin.\n")

    def check_adb(self):
        """Check if ADB is available in PATH (macOS-friendly)"""
        try:
            # prefer using `which adb` to ensure path presence on mac
            which = subprocess.run(["which", self.adb_path], capture_output=True, text=True)
            if which.returncode != 0 or not which.stdout.strip():
                return False
            result = subprocess.run([self.adb_path, "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def run_single_adb_command(self, command, format_output_func):
        """Execute ADB command and display formatted result."""
        command = command.replace("adb", self.adb_path)
        try:
            self.output_text.delete(1.0, tk.END)
            # if command is a string and includes pipes/redirects, run under shell
            # For safety, prefer list if possible. Many commands include pipes; keep shell=True but use shlex for repr
            process = subprocess.run(command, capture_output=True, text=True, shell=True)
            output = (process.stdout or "") + (process.stderr or "")
            formatted_output = format_output_func(output)
            self.output_text.insert(tk.END, formatted_output)
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}")

    """ --------------------- Formatters --------------------- """

    def format_devices(self, output):
        lines = [ln for ln in output.splitlines() if ln.strip()]
        # Expect header + devices; adb devices on mac prints "List of devices attached" then lines
        if not lines or all("device" not in ln for ln in lines[1:]):
            return "No devices connected!\n\nCommand run: \"adb devices\""
        devices = []
        for ln in lines[1:]:
            devices.append(ln.replace("\tdevice", " → Connected"))
        return "\n".join(devices) + "\n\nCommand run: \"adb devices\""

    def format_install(self, output):
        if "Success" in output or "success" in output.lower():
            return "Installation Successful!\n\nCommand run: \"adb install <APK_PATH>\""
        if "no devices" in output.lower():
            return "No devices connected!"
        return f"Installation Result:\n{output}\n\nCommand run: \"adb install <APK_PATH>\""

    def format_search(self, output):
        if not output.strip():
            return "No package found!\n\nCommand run: \"adb shell pm list packages | grep <PACKAGE_NAME>\""
        if "no devices" in output.lower():
            return "No devices connected!"
        # output lines like "package:com.example.app"
        return "\n".join([ln.replace("package:", "") for ln in output.splitlines() if ln.strip()]) + \
               "\n\nCommand run: \"adb shell pm list packages | grep <PACKAGE_NAME>\""

    def format_uninstall(self, output):
        if "Success" in output or "success" in output.lower():
            return "Uninstallation Successful!"
        if "no devices" in output.lower():
            return "No devices connected!"
        return f"Uninstallation Result:\n{output}\n\nCommand run: \"adb uninstall <PACKAGE_NAME>\""

    def format_sideload(self, output):
        if "failed" in output.lower():
            return "Make sure the device is in sideload mode and try again.\n(Select \"Apply update from ADB\" in Recovery Mode)\n\n" + output
        return f"Sideloading Finished. (Check output below.)\n\n{output}\n\nCommand run: \"adb sideload <FIRMWARE_PATH>.zip\""

    def format_shutdown(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Shutdown initiated\n\nCommand run: \"adb reboot -p\""

    def format_recovery(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Recovery initiated\n\nCommand run: \"adb reboot recovery\""

    def format_reboot(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Reboot initiated\n\nCommand run: \"adb reboot\""

    def format_back(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Back command executed\n\nCommand run: \"adb shell input keyevent 4\""

    def format_home(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Home command executed\n\nCommand run: \"adb shell input keyevent 3\""

    def format_applications(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Applications command executed\n\nCommand run: \"adb shell input keyevent 187\""

    def format_volume_up(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Volume Up command executed\n\nCommand run: \"adb shell input keyevent 24\""

    def format_power(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Power (Lock/Unlock) command executed\n\nCommand run: \"adb shell input keyevent 26\""

    def format_volume_down(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Volume Down command executed\n\nCommand run: \"adb shell input keyevent 25\""

    def format_settings(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Settings command executed\n\nCommand run: \"adb shell am start -n com.android.settings/.Settings\""

    def format_factory_test(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Factory Test command executed\n\nCommand run: \"adb shell am start -n com.ubx.factorykit/.Framework.Framework\""

    def format_push(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if "failed" in output.lower():
            return "Push failed. Check the local and device paths.\n\n" + output
        return f"File pushed successfully:\n{output}\n\nCommand run: \"adb push <LOCAL_PATH> <DEVICE_PATH>\""

    def format_storage(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return f"Device Storage:\n{output}\n\nCommand run: \"adb shell ls -l <DEVICE_PATH>\""

    def format_pull(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if "failed" in output.lower():
            return "Pull failed. Check the device and local paths.\n\n" + output
        return f"File pulled successfully:\n{output}\n\nCommand run: \"adb pull <DEVICE_PATH> <LOCAL_PATH>\""

    def format_screenshot(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if "failed" in output.lower():
            return "Screenshot failed. Check the device state.\n\n" + output
        return (
            f"Screenshot saved on device under /sdcard/Pictures/Screenshot_*.png\n"
            "You may pull it to your Mac with adb pull.\n\n"
            "Command run: \"adb shell screencap -p /sdcard/Pictures/<Screenshot_Timestamp>.png\""
        )

    def format_network(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if not output.strip():
            return "Network check returned no output. Device might be offline or command unsupported."
        return f"Network configuration:\n{output}\n\nCommand run: \"adb shell ifconfig\""

    def format_activity(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if "mCurrentFocus" not in output and "mFocusedApp" not in output:
            return "No current activity found. Output:\n" + output
        # try to extract the focused activity line:
        for ln in output.splitlines():
            if "mCurrentFocus" in ln or "mFocusedApp" in ln:
                return f"Current focus:\n{ln.strip()}\n\nCommand run: \"adb shell dumpsys window | grep mCurrentFocus\""
        return "Current activity (raw output):\n" + output

    def format_text(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return "Text entered.\n\nCommand run: \"adb shell input text <TEXT>\""

    def format_command(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        return output

    def format_start_activity(self, output):
        if "no devices" in output.lower():
            return "No devices connected!"
        if "Error" in output or "not found" in output.lower():
            return "Failed to start activity. Check the package/activity name.\n\n" + output
        return f"Activity started (or adb returned output):\n{output}\n\nCommand run: \"adb shell am start -n <PACKAGE_NAME>/<ACTIVITY_NAME>\""

    """ --------------------- Commands (button handlers) --------------------- """

    def run_adb_command_device_info(self):
        # list of properties to query; run them one by one
        props = [
            ("persist.sys.product.model", "Model Number"),
            ("pwv.project", "Project"),
            ("persist.sys.sw.version", "OS Version"),
            ("ro.ufs.build.version", "UFS version"),
            ("ro.serialno", "Serial Number"),
            ("ro.build.version.release", "Android version"),
            ("ro.build.version.sdk", "SDK(API) version")
        ]

        self.output_text.delete(1.0, tk.END)
        results = []
        for prop, _label in props:
            try:
                r = subprocess.run([self.adb_path, "shell", "getprop", prop], capture_output=True, text=True, check=True)
                results.append(r.stdout.strip() or "N/A")
            except subprocess.CalledProcessError:
                self.output_text.insert(tk.END, "No devices connected!\n")
                return
            except Exception as e:
                self.output_text.insert(tk.END, f"Error running adb: {e}\n")
                return

        # build output
        output_lines = ["Device Information:"]
        # combine model and project to mimic original behavior
        output_lines.append(f"Model Number: {results[0]}-{results[1]}")
        output_lines.append(f"{props[2][1]}: {results[2]}")
        output_lines.append(f"{props[3][1]}: {results[3]}")
        output_lines.append(f"{props[4][1]}: {results[4]}")
        output_lines.append(f"{props[5][1]}: {results[5]}")
        output_lines.append(f"{props[6][1]}: {results[6]}")

        self.output_text.insert(tk.END, "\n".join(output_lines) + "\n\nCommand run: \"adb shell getprop <property>\"")

    def run_install_apk(self):
        apk_path = self.install_apk_entry.get().strip()
        if not apk_path:
            self._show_error("Please enter a valid APK path")
            return
        apk_path = os.path.expanduser(apk_path)
        if not os.path.isfile(apk_path) or not apk_path.lower().endswith(".apk"):
            self._show_error("Please enter a valid APK path (file must exist and end with .apk)")
            return
        cmd = f'adb install "{apk_path}"'
        self.run_single_adb_command(cmd, self.format_install)

    def run_search_apk(self):
        apk_name = self.search_apk_entry.get().strip()
        if not apk_name:
            self._show_error("Please enter a valid APK/package name fragment")
            return
        # use grep (macOS/Unix), case-insensitive
        cmd = f'adb shell pm list packages | grep -i "{apk_name}"'
        self.run_single_adb_command(cmd, self.format_search)

    def run_uninstall_apk(self):
        apk_name = self.uninstall_apk_entry.get().strip()
        if not apk_name or "com." not in apk_name:
            self._show_error("Please enter a valid package name (e.g. com.example.app)")
            return
        cmd = f'adb uninstall "{apk_name}"'
        self.run_single_adb_command(cmd, self.format_uninstall)

    def run_sideload_firmware(self):
        firmware_path = os.path.expanduser(self.sideload_apk_entry.get().strip())
        if not firmware_path or not os.path.isfile(firmware_path) or not firmware_path.lower().endswith(".zip"):
            self._show_error("Please enter a valid firmware path (.zip)")
            return
        cmd = f'adb sideload "{firmware_path}"'
        self.run_single_adb_command(cmd, self.format_sideload)

    def run_check_storage(self):
        path = self.device_storage_entry.get().strip()
        if not path or not path.startswith("/sdcard/"):
            self._show_error("Please enter a valid device storage path (starting with /sdcard/)")
            return
        cmd = f'adb shell ls -l "{path}"'
        self.run_single_adb_command(cmd, self.format_storage)

    def run_adb_push(self):
        local_path = os.path.expanduser(self.push_local_entry.get().strip())
        device_path = self.push_device_entry.get().strip()

        if not local_path or not os.path.exists(local_path):
            self._show_error("Please enter a valid local file path")
            return
        if not device_path or not device_path.startswith("/sdcard/"):
            self._show_error("Please enter a valid device path (starting with /sdcard/)")
            return

        cmd = f'adb push "{local_path}" "{device_path}"'
        self.run_single_adb_command(cmd, self.format_push)

    def run_adb_pull(self):
        device_path = self.pull_device_entry.get().strip()
        local_path = os.path.expanduser(self.pull_local_entry.get().strip())

        if not device_path or not device_path.startswith("/sdcard/"):
            self._show_error("Please enter a valid device path (starting with /sdcard/)")
            return
        if not local_path:
            self._show_error("Please enter a valid local path")
            return

        cmd = f'adb pull "{device_path}" "{local_path}"'
        self.run_single_adb_command(cmd, self.format_pull)

    def run_text_input(self):
        text = self.text_input_entry.get().strip()
        if not text:
            self._show_error("Please enter some text")
            return
        # escape spaces for adb shell input text; adb expects certain escaping
        safe_text = text.replace('"', '\\"')
        cmd = f'adb shell input text "{safe_text}"'
        self.run_single_adb_command(cmd, self.format_text)

    def run_execute_command(self):
        command = self.text_input_entry.get().strip()
        if not command:
            self._show_error("Please enter a valid command")
            return
        # run exactly what user entered (assume adb shell commands or adb ...)
        self.run_single_adb_command(command, self.format_command)

    def run_start_activity(self):
        activity = self.start_activity_entry.get().strip()
        if not activity:
            self._show_error("Please enter a valid Package/Activity (e.g. com.example/.MainActivity)")
            return
        cmd = f'adb shell am start -n "{activity}"'
        self.run_single_adb_command(cmd, self.format_start_activity)

    def _show_error(self, msg):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Error: {msg}\n")

    """ --------------------- Build Controls UI --------------------- """

    def create_controls(self):
        # We'll build a grid of controls with sensible spacing.
        outer = self.controls_frame

        # Top row: device info & list devices
        top_row = ttk.Frame(outer)
        top_row.pack(fill=tk.X, pady=(4,8))
        ttk.Button(top_row, text="Get Device Info", width=18, command=self.run_adb_command_device_info).pack(side=tk.LEFT, padx=6)
        ttk.Button(top_row, text="List Devices", width=18, command=lambda: self.run_single_adb_command("adb devices", self.format_devices)).pack(side=tk.LEFT, padx=6)

        # Row: Install APK
        install_row = ttk.Frame(outer)
        install_row.pack(fill=tk.X, pady=4)
        desktop_default = os.path.join(os.path.expanduser("~"), "Desktop")
        self.install_apk_entry = ttk.Entry(install_row, width=86)
        self.install_apk_entry.pack(side=tk.LEFT, padx=(6,4))
        self.install_apk_entry.insert(0, desktop_default + os.sep)
        ttk.Button(install_row, text="Install APK", width=18, command=self.run_install_apk).pack(side=tk.LEFT, padx=6)

        # Row: Search & Uninstall
        search_row = ttk.Frame(outer)
        search_row.pack(fill=tk.X, pady=4)
        self.search_apk_entry = ttk.Entry(search_row, width=54)
        self.search_apk_entry.pack(side=tk.LEFT, padx=(6,4))
        ttk.Button(search_row, text="Search APK", width=18, command=self.run_search_apk).pack(side=tk.LEFT, padx=6)

        self.uninstall_apk_entry = ttk.Entry(search_row, width=54)
        self.uninstall_apk_entry.pack(side=tk.LEFT, padx=(12,4))
        ttk.Button(search_row, text="Uninstall APK", width=18, command=self.run_uninstall_apk).pack(side=tk.LEFT, padx=6)

        # Row: Sideload
        sideload_row = ttk.Frame(outer)
        sideload_row.pack(fill=tk.X, pady=4)
        self.sideload_apk_entry = ttk.Entry(sideload_row, width=86)
        self.sideload_apk_entry.pack(side=tk.LEFT, padx=(6,4))
        self.sideload_apk_entry.insert(0, desktop_default + os.sep)
        ttk.Button(sideload_row, text="Sideload firmware", width=18, command=self.run_sideload_firmware).pack(side=tk.LEFT, padx=6)

        # Row: System control (shutdown/recovery/reboot)
        sys_row = ttk.Frame(outer)
        sys_row.pack(fill=tk.X, pady=4)
        ttk.Button(sys_row, text="Shutdown", width=18, command=lambda: self.run_single_adb_command("adb reboot -p", self.format_shutdown)).pack(side=tk.LEFT, padx=10)
        ttk.Button(sys_row, text="Recovery Mode", width=18, command=lambda: self.run_single_adb_command("adb reboot recovery", self.format_recovery)).pack(side=tk.LEFT, padx=10)
        ttk.Button(sys_row, text="Reboot", width=18, command=lambda: self.run_single_adb_command("adb reboot", self.format_reboot)).pack(side=tk.LEFT, padx=10)

        # Row: Navigation/buttons
        nav_row = ttk.Frame(outer)
        nav_row.pack(fill=tk.X, pady=4)
        ttk.Button(nav_row, text="Back", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 4", self.format_back)).pack(side=tk.LEFT, padx=6)
        ttk.Button(nav_row, text="Home", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 3", self.format_home)).pack(side=tk.LEFT, padx=6)
        ttk.Button(nav_row, text="Applications", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 187", self.format_applications)).pack(side=tk.LEFT, padx=6)
        ttk.Button(nav_row, text="Volume Up", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 24", self.format_volume_up)).pack(side=tk.LEFT, padx=6)
        ttk.Button(nav_row, text="Lock/Unlock", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 26", self.format_power)).pack(side=tk.LEFT, padx=6)
        ttk.Button(nav_row, text="Volume Down", width=14, command=lambda: self.run_single_adb_command("adb shell input keyevent 25", self.format_volume_down)).pack(side=tk.LEFT, padx=6)

        # Row: Settings / Factory
        srow = ttk.Frame(outer)
        srow.pack(fill=tk.X, pady=4)
        ttk.Button(srow, text="Settings", width=20, command=lambda: self.run_single_adb_command("adb shell am start -n com.android.settings/.Settings", self.format_settings)).pack(side=tk.LEFT, padx=10)
        ttk.Button(srow, text="Factory Test", width=20, command=lambda: self.run_single_adb_command("adb shell am start -n com.ubx.factorykit/.Framework.Framework", self.format_factory_test)).pack(side=tk.LEFT, padx=10)

        # Row: Storage check
        storage_row = ttk.Frame(outer)
        storage_row.pack(fill=tk.X, pady=4)
        self.device_storage_entry = ttk.Entry(storage_row, width=86)
        self.device_storage_entry.pack(side=tk.LEFT, padx=(6,4))
        self.device_storage_entry.insert(0, "/sdcard/")
        ttk.Button(storage_row, text="Check Device Storage", width=18, command=self.run_check_storage).pack(side=tk.LEFT, padx=6)

        # Row: Push / Pull
        push_row = ttk.Frame(outer)
        push_row.pack(fill=tk.X, pady=4)
        self.push_local_entry = ttk.Entry(push_row, width=44)
        self.push_local_entry.pack(side=tk.LEFT, padx=(6,4))
        self.push_local_entry.insert(0, desktop_default + os.sep)
        ttk.Label(push_row, text="→").pack(side=tk.LEFT, padx=6)
        self.push_device_entry = ttk.Entry(push_row, width=30)
        self.push_device_entry.pack(side=tk.LEFT, padx=6)
        self.push_device_entry.insert(0, "/sdcard/")
        ttk.Button(push_row, text="Push File to device", width=18, command=self.run_adb_push).pack(side=tk.LEFT, padx=8)

        pull_row = ttk.Frame(outer)
        pull_row.pack(fill=tk.X, pady=4)
        self.pull_local_entry = ttk.Entry(pull_row, width=44)
        self.pull_local_entry.pack(side=tk.LEFT, padx=(6,4))
        self.pull_local_entry.insert(0, desktop_default + os.sep)
        ttk.Label(pull_row, text="←").pack(side=tk.LEFT, padx=6)
        self.pull_device_entry = ttk.Entry(pull_row, width=30)
        self.pull_device_entry.pack(side=tk.LEFT, padx=6)
        self.pull_device_entry.insert(0, "/sdcard/")
        ttk.Button(pull_row, text="Pull File from device", width=18, command=self.run_adb_pull).pack(side=tk.LEFT, padx=8)

        # Row: Screen capture / Network / Activity
        capture_row = ttk.Frame(outer)
        capture_row.pack(fill=tk.X, pady=4)
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        screenshot_cmd = f'adb shell screencap -p /sdcard/Pictures/Screenshot_{ts}.png'
        ttk.Button(capture_row, text="Screen Shot", width=18, command=lambda: self.run_single_adb_command(screenshot_cmd, self.format_screenshot)).pack(side=tk.LEFT, padx=10)
        ttk.Button(capture_row, text="Check Network", width=18, command=lambda: self.run_single_adb_command("adb shell ifconfig", self.format_network)).pack(side=tk.LEFT, padx=10)
        # on unix use grep for mCurrentFocus
        ttk.Button(capture_row, text="Check Activity", width=18, command=lambda: self.run_single_adb_command("adb shell dumpsys window | grep mCurrentFocus", self.format_activity)).pack(side=tk.LEFT, padx=10)

        # Row: Text input / Execute command
        text_row = ttk.Frame(outer)
        text_row.pack(fill=tk.X, pady=4)
        self.text_input_entry = ttk.Entry(text_row, width=68)
        self.text_input_entry.pack(side=tk.LEFT, padx=(6,4))
        ttk.Button(text_row, text="Execute Command", width=18, command=self.run_execute_command).pack(side=tk.LEFT, padx=6)
        ttk.Button(text_row, text="Enter Text", width=18, command=self.run_text_input).pack(side=tk.LEFT, padx=6)

        # Row: Start activity
        start_row = ttk.Frame(outer)
        start_row.pack(fill=tk.X, pady=6)
        self.start_activity_entry = ttk.Entry(start_row, width=86)
        self.start_activity_entry.pack(side=tk.LEFT, padx=(6,4))
        ttk.Button(start_row, text="Start Package/Activity", width=22, command=self.run_start_activity).pack(side=tk.LEFT, padx=6)


def main():
    try:
        print("Starting Tkinter application...")
        root = tk.Tk()
        print("Root window created")
        app = ADBTool(root)
        print("ADBTool instance created")
        root.mainloop()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()