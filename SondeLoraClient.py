from MeshtasticClient import MeshtasticClient
from DataOptimizer import DataOptimizer
from PacketLogger import PacketLogger
from SondeHubClient import SondeHubClient
from ConfigLoader import ConfigLoader
import json
import time


class SondeLoraClient:
    """
    Client that connects to a Meshtastic device and listens for CBOR-encoded
    sonde packets, then decodes and displays them.
    """

    def __init__(self, port=None, channel=None, source_device_id=None):
        """
        Initialize the sonde client.
        
        Args:
            port (str): Serial port of Meshtastic device (e.g., 'COM3', '/dev/ttyUSB0', '/dev/lilygo').
                       If None, will auto-detect.
            channel (int): Specific channel to listen on. If None, listens to all channels.
            source_device_id (int or str): Specific source device ID to listen to. 
                                        If None, listens to all sources.
        """
        self.optimizer = DataOptimizer()
        self.channel = channel
        self.source_device_id = source_device_id
        self.meshtastic_client = MeshtasticClient(
            port=port,
            receive_callback=self.on_message_received
        )
        
        # Initialize packet logger and SondeHub client
        self.packet_logger = PacketLogger()
        self.sondehub_client = SondeHubClient()
    
    def on_message_received(self, packet):
        """
        Callback function called when a message is received.
        
        Args:
            packet (dict): Message packet from Meshtastic device
        """
        try:
            valid_channel = True
            valid_source_device = True

            # Filter by channel if specified
            if self.channel is not None:
                packet_channel = packet.get("channel")
                if packet_channel != self.channel:
                    valid_channel = False

            # Filter by source device ID if specified
            if self.source_device_id is not None:
                from_id = packet.get("from")
                # Convert to same type for comparison
                source_id = int(self.source_device_id) if isinstance(self.source_device_id, str) else self.source_device_id
                if from_id != source_id:
                    valid_source_device = False
            
            # Ignore this packet if both filters do not match
            if ((self.channel and not valid_channel) or (self.source_device_id and not valid_source_device)):
                return

            # Check if packet has text content (hex-encoded CBOR data)
            if "decoded" in packet and "text" in packet["decoded"]:
                text_payload = packet["decoded"]["text"]
                
                # Try to decode as hex CBOR
                try:
                    cbor_bytes = bytes.fromhex(text_payload)
                    decoded_data = self.optimizer.from_cbor2(cbor_bytes)
                    
                    print(f"Text message received: {text_payload}\n")
                    print("="*50)
                    print("SONDE DATA RECEIVED")
                    print("="*50)
                    print(json.dumps(decoded_data, indent=2))
                    print("="*50 + "\n")
                    
                    # Log the decoded packet
                    self.packet_logger.log_packet(decoded_data)

                    # Send to SondeHub
                    self.sondehub_client.send_packet(decoded_data)

                except Exception as e:
                    pass
                    #print(f"Could not decode as CBOR: {e}")
        
        except Exception as e:
            print(f"Error processing received packet: {e}")
    
    def connect(self):
        """
        Connect to the Meshtastic device and start listening for packets.
        
        Returns:
            bool: True if connected successfully, False otherwise.
        """
        return self.meshtastic_client.connect()
    
    def disconnect(self):
        """Disconnect from the Meshtastic device."""
        self.meshtastic_client.disconnect()
    
    def listen(self):
        """
        Start listening for messages. This blocks until interrupted.
        """
        try:
            print("Listening for sonde packets...")
            print("Press Ctrl+C to stop.\n")
            
            # Keep the listener running
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nStopping listener...")
            self.disconnect()


if __name__ == "__main__":
    # Load config
    config = ConfigLoader.load_config()

    meshtastic_port = config.get("client", {}).get("meshtastic_port", None)
    channel = config.get("client", {}).get("channel", None)
    source_device_id = config.get("client", {}).get("source_device_id", None)

    client = SondeLoraClient(port=meshtastic_port, channel=channel, source_device_id=source_device_id)

    if client.connect():
        print(f"Connected on port: {meshtastic_port}")
        print(f"Listening on channel: {channel}")
        print(f"Source device ID: {source_device_id}")
        client.listen()
    else:
        print("Failed to connect to Meshtastic device")
