# 🎈 SondeLoraBridge 🖧
Forwards radiosonde telemetry packets over LoRa (Meshtastic)

🌐 [website](https://4z1kd.github.io/sonde-lora-bridge/) &nbsp;&nbsp;&nbsp;&nbsp; 💻 [dashboard](https://4z1kd.github.io/sonde-lora-bridge/dashboard.html)

## ⚠️ Important Note

**The SondeLoraBridge comes hand-in-hand with the SondeLoraClient.** You do **not** have to install both.
- **Bridge:** Install `SondeLoraBridge` if you have [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx/) installed and you want to forward the radiosonde packets over LoRa.
- **Client:** Install `SondeLoraClient` if you want to receive LoRa packets and forward them to SondeHub or another service.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/4Z1KD/sonde-lora-bridge.git
cd sonde-lora-bridge
```

---

### 2. Create a virtual environment
Make sure you have venv installed
```bash
sudo apt install python3.12-venv
```
Create the venv
```bash
python3 -m venv venv312
```

Activate it:

```bash
source venv312/bin/activate
```

---

### 3. Install requirements

```bash
cat requirements.txt | xargs -n 1 pip install
```

---

## LoRa Device Setup (Ubuntu)

On Ubuntu, it is recommended to create a **static symlink** for the LoRa (LilyGO) device so the serial port name remains stable across reboots.

### 4. Identify the USB device

```bash
lsusb
```

Note the `idVendor` and `idProduct` of your LoRa device.

### 5. Create a udev rule

#### 5.1 Open a new udev rules file

```bash
sudo nano /etc/udev/rules.d/99-lilygo.rules
```

#### 5.2 Add the rule (example)

```text
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d4", SYMLINK+="lilygo"
```

Adjust `idVendor` and `idProduct` if your device differs.

#### 5.3 Reload udev rules

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

The device will now be available as:

```text
/dev/lilygo
```

Add your user to the dialog group
```bash
sudo usermod -aG dialout $USER
```

Use this value when configuring `meshtastic_port`.

---

## Configuration

### 6. Edit the configuration file

Configure the following parameters:

- **host** – IP address of the `auto_rx` machine. Use `0.0.0.0` to accept packets from all IPs.
- **port** – UDP/TCP port to listen on.
- **count_threshold** – Transmit over LoRa every *N* received packets.
- **time_threshold** – Transmit over LoRa every *N* seconds.
- **meshtastic_reboot_interval** – Reboot the LoRa device every *N* seconds.
- **meshtastic_port** – Serial port of the LoRa device (e.g. `/dev/lilygo`).
- **target_device_id** – Only send packets to this specific Meshtastic device ID.
- **channel** – Meshtastic channel to transmit on.

---

## Running the Application

### 7. Create a run script

#### 7.1 Create the script

```bash
sudo nano /home/[YOUR_USER]/run_sonde_lora_bridge.sh
```

#### 7.2 Script contents

```bash
#!/usr/bin/env bash
# Fail fast if anything goes wrong
set -e

# Absolute path to the project
PROJECT_DIR="/home/[YOUR_USER]/sonde-lora-bridge"

# Activate virtual environment
source "$PROJECT_DIR/venv312/bin/activate"

# Run the application
python "$PROJECT_DIR/SondeLoraBridge.py"
```

Make it executable:

```bash
sudo chmod +x /home/[YOUR_USER]/run_sonde_lora_bridge.sh
```

---

## systemd Service

To ensure SondeLoraBridge starts automatically after reboot and restarts on failure, create a `systemd` service.

### 8. Create the service file

```bash
sudo nano /etc/systemd/system/sonde-lora-bridge.service
```

### 8.1 Service definition

```ini
[Unit]
Description=Start sonde-lora-bridge
BindsTo=dev-lilygo.device
After=dev-lilygo.device
Wants=dev-lilygo.device

[Service]
Type=simple
User=[YOUR_USER]
WorkingDirectory=/home/[YOUR_USER]
ExecStart=/home/[YOUR_USER]/run_sonde_lora_bridge.sh
Restart=always
RestartSec=10

[Install]
WantedBy=dev-lilygo.device
```

> **Note:** The device name must match the udev symlink (`/dev/lilygo`).

### 8.2 Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl disable sonde-lora-bridge.service
sudo systemctl enable sonde-lora-bridge.service
sudo systemctl start sonde-lora-bridge.service
```

Check status:

```bash
systemctl status sonde-lora-bridge.service
```

---

## Notes

- Ensure the LoRa device is connected before the service starts.
- Logs can be viewed using:
  ```bash
  journalctl -u sonde-lora-bridge.service -f
  ```
- The service is configured to automatically restart if it exits or the device reconnects.
<br>

# 🎈 SondeLoraClient 🖧
Receive LoRa packets, display, log and forward them to SondeHub

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/4Z1KD/sonde-lora-bridge.git
cd sonde-lora-bridge
```

---

### 2. Create a virtual environment

```bash
python3 -m venv venv312
```

Activate it:

```bash
/venv312/Scripts/activate
```

---

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Create a batch file
```bash
@echo off
REM Activate the virtual environment
call C:\[PATH TO YOUR VENV]\Scripts\activate
REM Run your Python script
python C:\[PATH TO YOUR PROJECT]\sonde-lora-bridge\gui.py
exit
```
<img width="1600" height="869" alt="image" src="https://github.com/user-attachments/assets/65705dfd-a001-432c-906d-b0bcfc2ec367" />
