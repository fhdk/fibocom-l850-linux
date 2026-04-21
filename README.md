# LTE Linux - Fibocom L850 (XMM7360) Setup

Complete Linux solution for the **Fibocom L850-GL** LTE modem (Intel XMM7360 chipset) with GUI system tray applet.

**Original project:**

**Tested on:** Linux Mint 22, Ubuntu 24.04  
**Hardware:** ThinkPad X1 Carbon with Fibocom L850-GL  
**Carrier:** Orange France (roaming in Belgium)

This project is a fork of [binghamfluid/xmm7360-deamon](https://github.com/binghamfluid/xmm7360-deamon) with adjustments for Manjaro Linux.

**Tested on:** Manjaro Linux
**Hardware:** ThinkPad T495 with Fibocom L850-GL
**Carrier:** Lebara (roaming in Denmark using Telenor)

![LTE Applet Screenshot](docs/screenshot.png)

## Features

- **Full LTE connectivity** without ModemManager
- **System tray applet** with signal strength indicator
- **Instant suspend/resume** (no modem reset required)
- **Auto WiFi switching** (WiFi off when LTE on)
- **Command-line control** (`lte on/off/suspend/resume/status`)
- **Auto-start on boot**
- **No password prompts** for network changes
- **Real-time quality monitoring** (latency, packet loss)

## Why This Project?

The Intel XMM7360 modem in the Fibocom L850 doesn't work with standard Linux tools (ModemManager). This project provides a complete solution with:
- Custom Python daemon for XMM7360 RPC protocol
- GTK system tray applet for easy control
- Proper integration with NetworkManager
- Quality-of-life features like instant suspend/resume

## Requirements

- **Hardware:** Fibocom L850-GL or other XMM7360-based modem
- **OS:** Linux Mint 22 / Ubuntu 24.04 / Debian-based distro
- **Kernel:** 6.x with `iosm` driver
- **Desktop:** GNOME, Cinnamon, or compatible (AppIndicator support)
- **SIM:** PIN must be disabled

## Quick Start

### 1. Fork and Clone Repository
Fork this repository and clone it to your local machine.

```bash
git clone https://github.com/YOUR_USERNAME/orange-lte-linux.git
cd orange-lte-linux
```

### 2. Run Installer
```bash
chmod +x install.sh
./install.sh
```

Ensure you have the following packages on your Manjaro system

- `systemd-resolvconf`
- `libayatana-appindicator`

```bash
sudo pacman -S systemd-resolvconf libayatana-appindicator
```

Configure your system to use `systemd-resolved`

```bash
sudo systemctl enable --now systemd-resolved
```
```bash
ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
```


### 3. Configure APN
Edit the systemd service file:
```bash
sudo micro /etc/systemd/system/xmm7360.service
``` 
Change the APN to match your carrier:
```ini
ExecStart=/usr/local/bin/xmm7360-daemon-full.py --apn YOUR_APN
```

Common APNs:
- Telenor Danmark: `internet`
- Orange France: `orange`
- Vodafone: `web.vodafone.de`
- T-Mobile: `internet.t-mobile`

### 4. Disable SIM PIN

**Critical:** Use a phone to disable PIN lock on your SIM card before first use.

### 5. Start Services
```bash
# Start LTE daemon
sudo systemctl start xmm7360

# Start applet
~/.local/bin/lte-applet.py &
```

### 6. Reboot (Recommended)
```bash
sudo reboot
```

After reboot, LTE will auto-connect and the applet will appear in your system tray.

## Usage

### System Tray Applet

Click the cellular icon in your system tray:
- **Status**: Connected/Suspended/Disconnected
- **IP Address**: Current LTE IP
- **Quality**: Signal quality with latency/loss
- **Connect/Disconnect**: Full modem control
- **Suspend/Resume**: Instant on/off (no modem reset)
- **Restart**: Full restart (takes 5-6 minutes)
- **Show Logs**: View daemon logs

### Command Line
```bash
lte on          # Connect LTE (takes 1-2 min on first start)
lte off         # Disconnect LTE completely
lte suspend     # Quick disable (instant, keeps daemon running)
lte resume      # Quick enable (instant)
lte status      # Show connection status with quality
lte restart     # Full restart
lte logs        # View live logs
```

### Auto WiFi Switching

When LTE connects → WiFi automatically turns OFF  
When LTE disconnects → WiFi automatically turns ON  

This ensures only one connection is active.

## Configuration

### Change APN
```bash
sudo nano /etc/systemd/system/xmm7360.service
# Change: --apn YOUR_APN
sudo systemctl daemon-reload
sudo systemctl restart xmm7360
```

### Disable Auto-Start
```bash
sudo systemctl disable xmm7360
rm ~/.config/autostart/lte-applet.desktop
```

### Disable Auto WiFi Switching

Edit `~/.local/bin/lte-applet.py` and comment out the `manage_wifi()` calls.

## Troubleshooting

### LTE Won't Connect

```bash
# Check daemon logs
sudo journalctl -u xmm7360 -n 50

# Check modem device
ls -la /dev/wwan0*

# Check if ModemManager is interfering
systemctl status ModemManager
# Should show: masked, inactive

# Try manual start
sudo systemctl restart xmm7360
```

### Applet Not Showing

Check if the dependency on libayatane has been added to your system.

```bash
# Check if running
ps aux | grep lte-applet

# Start manually
~/.local/bin/lte-applet.py

# Check for errors in terminal output
```

### Can't Resume After Suspend

This is normal, wait 10 to 15 seconds for the UI to update after clicking Resume.

### Connection Takes 5+ Minutes After Restart

This is expected, the modem hardware needs time to reset after being stopped. Use **Suspend/Resume** instead for instant on/off.

## Project Structure
```
fibocom-lte-linux/
├── src/
│   ├── daemon/
│   │   └── xmm7360-daemon-full.py    # Main LTE daemon
│   ├── applet/
│   │   ├── lte-applet.py             # GTK system tray applet
│   │   └── lte-applet.desktop        # Auto-start config
│   ├── scripts/
│   │   ├── lte                       # Control script
│   │   ├── configure-wwan0-post.sh   # Post-connection config
│   │   └── modem-reset.sh            # Modem reset script
│   └── systemd/
│       ├── xmm7360.service           # Systemd service
│       └── lte-nopasswd.example      # Sudoers config
├── install.sh                        # Main installer
├── README.md                         # This file
└── LICENSE                           # GPL-2.0
```

## Contributing

Contributions welcome! This project was developed through extensive troubleshooting on a ThinkPad X1 Carbon.

### Areas for Improvement

- [ ] Real signal strength monitoring (AT commands)
- [ ] SMS support
- [ ] IPv6 support
- [ ] Multiple carrier profiles
- [ ] GUI for APN configuration
- [ ] Support for other XMM7360 modems

## License

GPL-2.0 (same as xmm7360-pci project)

## Credits

- **xmm7360-pci project**: Original kernel driver and RPC implementation
- **binghamfluid/xmm7360-deamon**: Python daemon foundation
- **Claude.ai**: Development assistance

##  Known Limitations

- No ModemManager support (incompatible with XMM7360)
- SIM PIN must be disabled
- No signal strength from AT commands (uses latency instead)
- Restart takes 5+ minutes due to hardware reset requirement
- IPv6 may require additional configuration

## Support

For issues specific to this setup, please open a GitHub issue.

For general XMM7360 issues, see:
- [xmm7360-pci](https://github.com/xmm7360/xmm7360-pci)
- [binghamfluid/xmm7360-deamon](https://github.com/binghamfluid/xmm7360-deamon)

---

Original project: Made with ❤️ for the Linux community xx Claude for coding assistance

