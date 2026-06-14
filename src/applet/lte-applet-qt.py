#!/usr/bin/env python3
import sys
import subprocess
import re

try:
    from PyQt5.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
    )
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import QTimer, Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QMessageBox
    )
    from PyQt6.QtGui import QIcon, QAction
    from PyQt6.QtCore import QTimer, Qt


class LTEApplet:
    def __init__(self, app):
        self.app = app
        self._last_icon = None
        self._last_status = None

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon.fromTheme("network-cellular-offline"))
        self.tray.setToolTip("LTE Status")

        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(3000)
        self.update_status()

    def _build_menu(self):
        self.menu.clear()

        self.status_action = QAction("Checking...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.ip_action = QAction("IP: --.--.--.--", self.menu)
        self.ip_action.setEnabled(False)
        self.menu.addAction(self.ip_action)

        self.quality_action = QAction("Quality: Unknown", self.menu)
        self.quality_action.setEnabled(False)
        self.menu.addAction(self.quality_action)

        self.menu.addSeparator()

        self.toggle_action = QAction("Connect", self.menu)
        self.toggle_action.triggered.connect(self.toggle_connection)
        self.menu.addAction(self.toggle_action)

        self.suspend_action = QAction("Suspend", self.menu)
        self.suspend_action.triggered.connect(self.toggle_suspend)
        self.menu.addAction(self.suspend_action)

        self.menu.addSeparator()

        restart_action = QAction("Restart", self.menu)
        restart_action.triggered.connect(self.restart_connection)
        self.menu.addAction(restart_action)

        logs_action = QAction("Show Logs", self.menu)
        logs_action.triggered.connect(self.show_logs)
        self.menu.addAction(logs_action)

        self.menu.addSeparator()

        quit_action = QAction("Quit Applet", self.menu)
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)

    def set_icon_and_label(self, icon_name):
        if self._last_icon != icon_name:
            self.tray.setIcon(QIcon.fromTheme(icon_name))
            self._last_icon = icon_name
        self.tray.setToolTip("LTE Status")

    def manage_wifi(self, enable):
        try:
            if enable:
                subprocess.run(['nmcli', 'radio', 'wifi', 'on'], check=False)
            else:
                subprocess.run(['nmcli', 'radio', 'wifi', 'off'], check=False)
        except Exception:
            pass

    def update_status(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'xmm7360'],
                                    capture_output=True, text=True, timeout=2)

            if result.stdout.strip() == 'active':
                ip_result = subprocess.run(['ip', 'addr', 'show', 'wwan0'],
                                           capture_output=True, text=True, timeout=2)

                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)

                if ip_match:
                    ip = ip_match.group(1)

                    is_up = False

                    if 'state UP' in ip_result.stdout or 'UP,LOWER_UP' in ip_result.stdout:
                        is_up = True
                    elif '<POINTOPOINT,NOARP,UP,LOWER_UP>' in ip_result.stdout or '<UP,' in ip_result.stdout:
                        is_up = True

                    if not is_up:
                        try:
                            with open('/sys/class/net/wwan0/operstate', 'r') as f:
                                state = f.read().strip()
                                if state in ['up', 'unknown']:
                                    is_up = True
                        except Exception:
                            pass

                    if not is_up and ip_match:
                        quick_ping = subprocess.run(
                            ['ping', '-I', 'wwan0', '-c', '1', '-W', '1', '8.8.8.8'],
                            capture_output=True, text=True, timeout=3)
                        if quick_ping.returncode == 0:
                            is_up = True

                    print(f"DEBUG: IP={ip}, is_up={is_up}")

                    if is_up:
                        print(f"DEBUG: Interface detected as UP, testing connectivity...")
                        ping_result = subprocess.run(
                            ['ping', '-I', 'wwan0', '-c', '2', '-W', '2', '8.8.8.8'],
                            capture_output=True, text=True, timeout=5)

                        if ping_result.returncode == 0:
                            latency_match = re.search(
                                r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/', ping_result.stdout)
                            latency = int(float(latency_match.group(1))) if latency_match else None

                            loss_match = re.search(r'(\d+)% packet loss', ping_result.stdout)
                            loss = int(loss_match.group(1)) if loss_match else 100

                            if latency and latency < 50 and loss == 0:
                                quality = "Excellent"
                                icon = "network-cellular-signal-excellent"
                            elif latency and latency < 100 and loss < 10:
                                quality = "Good"
                                icon = "network-cellular-signal-good"
                            elif latency and latency < 150 and loss < 20:
                                quality = "Fair"
                                icon = "network-cellular-signal-ok"
                            elif latency and latency < 200 and loss < 30:
                                quality = "Poor"
                                icon = "network-cellular-signal-weak"
                            else:
                                quality = "Very Poor"
                                icon = "network-cellular-signal-none"

                            print(f"DEBUG: Connected - Quality: {quality}, Latency: {latency}ms")

                            new_status = "Connected"
                            if self._last_status != new_status:
                                print(f"DEBUG: Status changed from {self._last_status} to {new_status}")
                                self._last_status = new_status

                            self.status_action.setText("Status: Connected")
                            self.ip_action.setText(f"IP: {ip}")
                            if latency:
                                self.quality_action.setText(f"{quality} | {latency}ms | Loss: {loss}%")
                            else:
                                self.quality_action.setText(f"Quality: {quality}")

                            self.set_icon_and_label(icon)
                            self.toggle_action.setText("Disconnect")
                            self.suspend_action.setText("Suspend")
                            self.suspend_action.setEnabled(True)
                        else:
                            print(f"DEBUG: Ping failed, checking route...")
                            route_check = subprocess.run(
                                ['ip', 'route', 'show', 'dev', 'wwan0'],
                                capture_output=True, text=True, timeout=2)
                            if route_check.stdout.strip():
                                print(f"DEBUG: Route exists but no ping response")
                                self.status_action.setText("Status: No Internet")
                                self.ip_action.setText(f"IP: {ip}")
                                self.quality_action.setText("Quality: No connectivity")
                                self.set_icon_and_label("network-cellular-signal-none")
                            else:
                                print(f"DEBUG: No route, still resuming")
                                self.status_action.setText("Status: Resuming...")
                                self.ip_action.setText(f"IP: {ip}")
                                self.quality_action.setText("Quality: Configuring...")
                                self.set_icon_and_label("network-cellular-acquiring")

                            self.toggle_action.setText("Disconnect")
                            self.suspend_action.setText("Suspend")
                            self.suspend_action.setEnabled(True)
                    else:
                        print(f"DEBUG: Interface detected as DOWN/suspended")

                        new_status = "Suspended"
                        if self._last_status != new_status:
                            print(f"DEBUG: Status changed from {self._last_status} to {new_status}")
                            self._last_status = new_status

                        self.status_action.setText("Status: Suspended")
                        self.ip_action.setText(f"IP: {ip} (inactive)")
                        self.quality_action.setText("Quality: Interface down")
                        self.set_icon_and_label("network-cellular-offline")
                        self.toggle_action.setText("Disconnect")
                        self.suspend_action.setText("Resume")
                        self.suspend_action.setEnabled(True)
                else:
                    print(f"DEBUG: No IP detected, daemon connecting...")
                    self.status_action.setText("Status: Connecting...")
                    self.ip_action.setText("IP: Waiting...")
                    self.quality_action.setText("Quality: Unknown")
                    self.set_icon_and_label("network-cellular-acquiring")
                    self.toggle_action.setText("Disconnect")
                    self.suspend_action.setEnabled(False)
            else:
                print(f"DEBUG: xmm7360 service not active")

                new_status = "Disconnected"
                if self._last_status != new_status:
                    print(f"DEBUG: Status changed from {self._last_status} to {new_status}")
                    self._last_status = new_status

                self.status_action.setText("Status: Disconnected")
                self.ip_action.setText("IP: --.--.--.--")
                self.quality_action.setText("Quality: N/A")
                self.set_icon_and_label("network-cellular-offline")
                self.toggle_action.setText("Connect")
                self.suspend_action.setEnabled(False)

        except Exception as e:
            print(f"DEBUG: Exception in update_status: {e}")
            self.status_action.setText("Status: Error")
            self.ip_action.setText(f"Error: {str(e)[:30]}")
            self.quality_action.setText("")
            self.set_icon_and_label("dialog-error")

    def toggle_connection(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'xmm7360'],
                                    capture_output=True, text=True)

            if result.stdout.strip() == 'active':
                subprocess.Popen(['sudo', '/usr/local/bin/lte', 'off'])
                self.show_notification("LTE", "Disconnecting... WiFi will be enabled")
                QTimer.singleShot(5000, lambda: self.manage_wifi(True))
            else:
                self.show_notification("LTE", "Connecting... WiFi will be disabled (takes 1-2 min)")
                subprocess.Popen(['sudo', '/usr/local/bin/lte', 'on'])
                QTimer.singleShot(90000, lambda: self.manage_wifi(False))
        except Exception as e:
            self.show_notification("LTE Error", str(e))

    def toggle_suspend(self):
        try:
            ip_result = subprocess.run(['ip', 'addr', 'show', 'wwan0'],
                                       capture_output=True, text=True)

            if 'state UP' in ip_result.stdout or 'UP' in ip_result.stdout:
                result = subprocess.run(['sudo', '/usr/local/bin/lte', 'suspend'],
                                        capture_output=True, text=True)
                print("Suspend output:", result.stdout, result.stderr)
                self.show_notification("LTE", "Suspended - WiFi enabled")
                self.manage_wifi(True)
                self.status_action.setText("Status: Suspended")
                self.suspend_action.setText("Resume")
                self.set_icon_and_label("network-cellular-offline")
                QTimer.singleShot(100, self.update_status)
            else:
                print("Attempting to resume LTE...")

                self.status_action.setText("Status: Resuming...")
                self.quality_action.setText("Quality: Connecting...")
                self.suspend_action.setText("Suspend")
                self.set_icon_and_label("network-cellular-acquiring")

                result = subprocess.run(['sudo', '/usr/local/bin/lte', 'resume'],
                                        capture_output=True, text=True)
                print("Resume output:", result.stdout)

                self.show_notification("LTE", "Resumed - WiFi disabled")

                self.manage_wifi(False)

                for delay in [100, 300, 600, 1000, 1500, 2000]:
                    QTimer.singleShot(delay, self.update_status)

        except Exception as e:
            print("Error in toggle_suspend:", str(e))
            self.show_notification("LTE Error", str(e))

    def restart_connection(self):
        subprocess.Popen(['sudo', '/usr/local/bin/lte', 'restart'])
        self.show_notification("LTE", "Restarting... (may take several minutes)")
        self.manage_wifi(True)
        QTimer.singleShot(360000, lambda: self.manage_wifi(False))

    def show_logs(self):
        for terminal in (
            ['konsole', '-e', 'bash', '-c', 'sudo journalctl -u xmm7360 -f; exec bash'],
            ['gnome-terminal', '--', 'bash', '-c', 'sudo journalctl -u xmm7360 -f; exec bash'],
            ['xterm', '-e', 'bash', '-c', 'sudo journalctl -u xmm7360 -f; exec bash'],
        ):
            try:
                subprocess.Popen(terminal)
                return
            except FileNotFoundError:
                continue

    def show_notification(self, title, message):
        try:
            subprocess.run(['notify-send', title, message, '-i', 'network-cellular'])
        except Exception:
            pass

    def quit(self):
        self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "LTE Applet",
                             "System tray is not available on this desktop.")
        sys.exit(1)

    applet = LTEApplet(app)
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())
