from MeshtasticClient import MeshtasticClient
from DataOptimizer import DataOptimizer
from PacketLogger import PacketLogger
from ConfigLoader import ConfigLoader
import json
import time


class SondeLoraClient:
    """
    Client that connects to a Meshtastic device and listens for CBOR-encoded
    sonde packets, then decodes and displays them.
    """
    
    def __init__(self, port=None, channel=None, source_node_id=None):
        """
        Initialize the sonde client.
        
        Args:
            port (str): Serial port of Meshtastic device (e.g., 'COM3', '/dev/ttyUSB0', '/dev/lilygo').
                       If None, will auto-detect.
            channel (int): Specific channel to listen on. If None, listens to all channels.
            source_node_id (int or str): Specific source node ID to listen to. 
                                        If None, listens to all sources.
        """
        self.optimizer = DataOptimizer()
        self.channel = channel
        self.source_node_id = source_node_id
        self.meshtastic_client = MeshtasticClient(
            port=port,
            receive_callback=self.on_message_received
        )
        
        # Initialize packet logger
        self.packet_logger = PacketLogger()
    
    def on_message_received(self, packet):
        #print("Packet received:", packet)
        """
        Callback function called when a message is received.
        
        Args:
            packet (dict): Message packet from Meshtastic device
        """
        try:
            # Filter by channel if specified
            if self.channel is not None:
                packet_channel = packet.get("channel", 0)
                if packet_channel != self.channel:
                    return
            
            # Filter by source node ID if specified
            if self.source_node_id is not None:
                from_id = packet.get("from")
                # Convert to same type for comparison
                source_id = int(self.source_node_id) if isinstance(self.source_node_id, str) else self.source_node_id
                if from_id != source_id:
                    return
            
            # Check if packet has text content (hex-encoded CBOR data)
            if "decoded" in packet and "text" in packet["decoded"]:
                text_payload = packet["decoded"]["text"]
                print(f"\nText message received: {text_payload}")
                
                # Try to decode as hex CBOR
                try:
                    cbor_bytes = bytes.fromhex(text_payload)
                    decoded_data = self.optimizer.from_cbor2(cbor_bytes)
                    
                    print("\n" + "="*50)
                    print("SONDE DATA RECEIVED")
                    print("="*50)
                    print(json.dumps(decoded_data, indent=2))
                    print("="*50 + "\n")
                    
                    # Log the decoded packet
                    self.packet_logger.log_packet(decoded_data)
                    
                except Exception as e:
                    print(f"Could not decode as CBOR: {e}")
        
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

    client_port = config.get("client", {}).get("meshtastic_port", None)

    client = SondeLoraClient(port=client_port)

    if client.connect():
        client.listen()
    else:
        print("Failed to connect to Meshtastic device")
