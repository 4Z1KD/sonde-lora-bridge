from DataReceiver import DataReceiver
from WorkloadManager import WorkloadManager
from DataOptimizer import DataOptimizer
from MeshtasticClient import MeshtasticClient
from datetime import datetime, timezone
import json
import threading
import time


class SondeLoraBridge:
    """
    Connects a UDP listener to a workload manager.
    Receives raw UDP data and passes it to the manager.
    The manager buffers data and triggers decoding.
    """

    def __init__(self, host='0.0.0.0', port=8080, count_threshold=10, 
                 time_threshold=15):
        """
        Initialize the bridge.

        Args:
            host (str): UDP host to listen on
            port (int): UDP port to listen on
            count_threshold (int): Number of items before triggering processing
            time_threshold (float): Time in seconds before triggering processing
        """
        # Create the workload manager with internal callback
        self.manager = WorkloadManager(
            count_threshold=count_threshold,
            time_threshold=time_threshold,
            callback=self.process_data
        )

        # Create the UDP listener with callback to send data to manager
        self.listener = DataReceiver(
            host=host,
            port=port,
            callback=self._on_data_received
        )
        
        # Initialize the data optimizer
        self.optimizer = DataOptimizer()
        
        # Initialize Meshtastic client
        self.meshtastic_client = MeshtasticClient(port="COM4")
        self.target_device_id = None
        
        # Reboot timer
        self.reboot_thread = None
        self.reboot_interval = 3600  # 1 hour in seconds
        self.stop_reboot_timer = False

    def _on_data_received(self, data: str):
        """
        Internal callback that receives encoded data from listener
        and forwards it to the manager.

        Args:
            data (str): encoded data from the listener
        """
        if data:
            self.manager.receive(data)
            #print(data)
            #print(f"Data received and forwarded to manager: {len(data)} bytes")

    def start(self):
        """Start listening for UDP packets."""
        self.listener.listen()

    def stop(self):
        """Stop listening and flush any remaining data."""
        self.stop_reboot_timer = True
        self.manager.flush()
        if self.meshtastic_client.is_connected():
            self.meshtastic_client.disconnect()
    
    def start_reboot_timer(self, interval=3600):
        """
        Start a timer that periodically reboots the Meshtastic device.
        
        Args:
            interval (int): Interval in seconds between reboots (default: 3600 = 1 hour)
        """
        self.reboot_interval = interval
        self.stop_reboot_timer = False
        self.reboot_thread = threading.Thread(target=self._reboot_loop, daemon=True)
        self.reboot_thread.start()
        print(f"Reboot timer started with interval: {interval} seconds")
    
    def _reboot_loop(self):
        """Internal loop for periodic reboots."""
        while not self.stop_reboot_timer:
            time.sleep(self.reboot_interval)
            if not self.stop_reboot_timer and self.meshtastic_client.is_connected():
                print("Triggering periodic device reboot...")
                self.meshtastic_client.reboot()
    
    def stop_reboot_timer_func(self):
        """Stop the reboot timer."""
        self.stop_reboot_timer = True
        if self.reboot_thread:
            self.reboot_thread.join(timeout=5)
        print("Reboot timer stopped")
    
    def process_data(self, raw_data):
        """
        Process JSON payload summary data and create a minimal packet.

        Args:
            raw_data (str): JSON-encoded payload summary data
        """
        try:
            
            # Parse JSON data
            data = json.loads(raw_data)
            
            # Check if this is a PAYLOAD_SUMMARY type
            if data.get("type") != "PAYLOAD_SUMMARY":
                print(f"Unsupported packet type: {data.get('type')}")
                return
            
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            # Create minimal DTO from JSON fields
            dto = {
            #"type": data.get("type", ""),
            #"station": data.get("station", ""),
            "callsign": data.get("callsign", ""),
            "latitude": data.get("latitude", ""),
            "longitude": data.get("longitude", ""),
            "altitude": data.get("altitude", ""),
            #"speed": data.get("speed", ""),
            #"heading": data.get("heading", ""),
            "time": data.get("time", ""),
            #"comment": data.get("comment", ""),
            "model": data.get("model", ""),
            "freq": data.get("freq", ""),
            #"temp": data.get("temp", ""),
            "frame": data.get("frame", ""),
            #"humidity": data.get("humidity", ""),
            #"pressure": data.get("pressure", ""),
            #"sats": data.get("sats", ""),
            #"batt": data.get("batt", ""),
            #"sdr_device_idx": data.get("sdr_device_idx", ""),
            #"vel_v": data.get("vel_v", ""),
            #"vel_h": data.get("vel_h", ""),
            "bt": data.get("bt", ""), 
            "snr": data.get("snr", ""),
            "subtype": data.get("subtype", ""),
            }
            
            # Convert DTO to CBOR2
            cbor_data = self.optimizer.to_cbor2(dto)
            print(cbor_data.hex())
            
            # Send CBOR data via Meshtastic to target device
            if self.meshtastic_client.is_connected() and self.target_device_id:
                self.meshtastic_client.send_direct_message(
                    self.target_device_id,
                    f"{cbor_data.hex()}"
                )
                print(f"CBOR data sent to {self.target_device_id}")
            else:
                # connect if not connected
                print("Connecting to Meshtastic device...")
                if self.meshtastic_client.connect():
                    print("Connected to Meshtastic device.")
                    self.meshtastic_client.send_direct_message(
                        self.target_device_id,
                        f"{cbor_data.hex()}"
                    )
                    print(f"CBOR data sent to {self.target_device_id}")
                else:
                    print("Failed to connect to Meshtastic device.")
        
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"Error processing payload: {e}")
        


if __name__ == "__main__":
    bridge = SondeLoraBridge(
        host='0.0.0.0',
        port=8080,
        count_threshold=6,
        time_threshold=60
    )
    
    # Connect to Meshtastic device
    bridge.target_device_id = '!06f562b8'
    if bridge.meshtastic_client.connect():
        # Start reboot timer (every 1 hour)
        bridge.start_reboot_timer(interval=3600)
        
        bridge.start()
    else:
        print("Failed to connect to Meshtastic device")
        bridge.stop()
