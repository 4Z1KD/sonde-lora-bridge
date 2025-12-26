import requests
import json
from datetime import datetime, timezone
from ConfigLoader import ConfigLoader


class SondeHubClient:
    """
    Client for sending decoded sonde data to SondeHub.
    Handles all API communication with SondeHub endpoints.
    """

    # SondeHub API endpoint (PUT request)
    SONDEHUB_API_URL = "https://api.v2.sondehub.org/sondes/telemetry"

    def __init__(self):
        """Initialize the SondeHub client with configuration."""
        self.config = ConfigLoader.load_config()
        self.sondeHub_config = self.config.get("sondeHub", {})
        self.enabled = self.sondeHub_config.get("enabled", False)
        self.uploader_callsign = self.sondeHub_config.get("uploader_callsign", "N0CALL")
        self.uploader_position = self.sondeHub_config.get("uploader_position", None)
        self.uploader_antenna = self.sondeHub_config.get("uploader_antenna", "")
        self.timeout = 10  # Default timeout in seconds

    def send_packet(self, decoded_packet):
        """
        Send a decoded sonde packet to SondeHub.

        Args:
            decoded_packet (dict): The decoded sonde data containing at minimum:
                - datetime: ISO 8601 timestamp
                - lat: Latitude
                - lon: Longitude
                - alt: Altitude in meters
                - Other sonde-specific fields (frequency, serial, type, etc.)

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            # Prepare the payload for SondeHub (as an array of objects)
            payload = [self._prepare_payload(decoded_packet)]

            # Prepare headers as per SondeHub API spec
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "sonde-lora-bridge",
                "Date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            }

            # Send to SondeHub using PUT request
            response = requests.put(
                self.SONDEHUB_API_URL,
                json=payload,
                timeout=self.timeout,
                headers=headers
            )

            if response.status_code == 200:
                print(f"Packet sent to SondeHub")
                return True
            else:
                print(f"SondeHub error ({response.status_code}): {response.text}")
                return False

        except requests.exceptions.Timeout:
            print(f"SondeHub request timeout ({self.timeout}s)")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"SondeHub connection error: {e}")
            return False
        except Exception as e:
            print(f"Error sending to SondeHub: {e}")
            return False

    def _prepare_payload(self, decoded_packet):
        """
        Prepare the payload for SondeHub API.
        Follows the SondeHub telemetry schema.

        Args:
            decoded_packet (dict): The decoded sonde data

        Returns:
            dict: Single telemetry object formatted for SondeHub API
        """
        # Create telemetry object with required and optional fields
        telemetry = {
            "software_name": "sonde-lora-bridge",
            "software_version": "1.0",
            "uploader_callsign": self.uploader_callsign
        }

        # Convert field mappings from received packet keys to SondeHub keys
        field_mapping = {
            "model": "type",
            "callsign": "serial",
            "time": "datetime",
            "latitude": "lat",
            "longitude": "lon",
            "altitude": "alt",
        }
        
        # Apply field mappings to decoded_packet
        mapped_packet = decoded_packet.copy()
        for old_key, new_key in field_mapping.items():
            if old_key in mapped_packet and old_key != new_key:
                mapped_packet[new_key] = mapped_packet.pop(old_key)

        # Core location/altitude fields
        core_fields = ["dev", "datetime", "lat", "lon", "alt"]
        for field in core_fields:
            if field in mapped_packet:
                telemetry[field] = mapped_packet[field]

        # Sonde identification fields
        id_fields = ["manufacturer", "type", "serial", "subtype"]
        for field in id_fields:
            if field in mapped_packet:
                telemetry[field] = mapped_packet[field]

        # Telemetry fields
        telemetry_fields = [
            "frame", "freq", "temp", "humidity", "pressure",
            "vel_h", "vel_v", "heading", "batt", "sats",
            "xdata", "snr", "rssi"
        ]
        for field in telemetry_fields:
            if field in mapped_packet:
                telemetry[field] = mapped_packet[field]

        # Uploader information
        if self.uploader_position:
            telemetry["uploader_position"] = self.uploader_position
        if self.uploader_antenna:
            telemetry["uploader_antenna"] = self.uploader_antenna
        
        print(json.dumps(telemetry, indent=2))
        return telemetry

if __name__ == "__main__":
    # Test the SondeHubClient with sample data
    client = SondeHubClient()
    
    # Create sample decoded packet
    api_sample_packet = {
        "dev": "string",
        "type": "RS41",
        "serial": "W3610141",
        "datetime": "2025-12-25T20:43:44.964Z",
        "lat": 32.820282,
        "lon": 35.594825,
        "alt": 1000,
    }
    test_sample_packet = {
        "type": "PAYLOAD_SUMMARY",
        "station": "4Z1KD",
        "callsign": "W4944862",
        "latitude": 31.99835,
        "longitude": 34.82983,
        "altitude": 2391.92038,
        "speed": 7.381908000000001,
        "heading": 126.88162,
        "time": "2025-12-26T11:24:07",
        "comment": "Radiosonde",
        "model": "RS41-SGP",
        "freq": "405.3010 MHz",
        "temp": 0.9,
        "frame": 1308,
        "bt": 65535,
        "pressure": 761.26,
        "sats": 10,
        "batt": 2.9,
        "snr": 18.9,
        "fest": [
            -2250,
            2550
        ],
        "f_centre": 405301150,
        "ppm": 349.1111111111111,
        "subtype": "RS41-SGP",
        "sdr_device_idx": "0",
        "vel_v": 6.4233,
        "vel_h": 2.05053
    }
    
    print("Testing SondeHubClient...")
    print(f"SondeHub enabled: {client.enabled}")
    print(f"Uploader callsign: {client.uploader_callsign}")
    print("\nSample packet:")
    print(json.dumps(test_sample_packet, indent=2))
    print("\nPrepared payload:")
    payload = client._prepare_payload(test_sample_packet)
    print(json.dumps(payload, indent=2))
    
    if client.enabled:
        print("\nAttempting to send to SondeHub...")
        result = client.send_packet(test_sample_packet)
        print(f"Send result: {result}")
    else:
        print("\nSondeHub is disabled in config. Enable it to test sending.")
