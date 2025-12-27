# 🎈 SondeLoraBridge 🖧

forwards radiosonde telemetry packets over LoRa (Meshtastic)

🌐[website](https://4z1kd.github.io/sonde-lora-bridge/)

💻[dashboard](https://4z1kd.github.io/sonde-lora-bridge/dashboard.html)

---

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
source venv312/bin/activate
```

---

### 3. Install requirements

```bash
pip install -r requirements.txt
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
sudo nano /home/sonde/run_sonde_lora_bridge.sh
```

#### 7.2 Script contents

```bash
#!/usr/bin/env bash
# Fail fast if anything goes wrong
set -e

# Absolute path to the project
PROJECT_DIR="/home/sonde/sonde-lora-bridge"

# Activate virtual environment
source "$PROJECT_DIR/venv312/bin/activate"

# Run the application
python "$PROJECT_DIR/SondeLoraBridge.py"
```

Make it executable:

```bash
chmod +x /home/sonde/run_sonde_lora_bridge.sh
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
User=sonde
WorkingDirectory=/home/sonde
ExecStart=/home/sonde/run_sonde_lora_bridge.sh
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

---
