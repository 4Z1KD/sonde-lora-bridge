import meshtastic
import meshtastic.serial_interface
import time
from pubsub import pub


class MeshtasticClient:
    """
    Connects to a local Meshtastic device over serial and provides messaging capabilities.
    """
    
    def __init__(self, port=None, receive_callback=None):
        """
        Initialize the Meshtastic client.
        
        Args:
            port (str): Serial port (e.g., '/dev/ttyUSB0', 'COM3'). 
                       If None, will auto-detect.
            receive_callback (callable): Function to call when messages are received.
                                        Receives message dict as parameter.
        """
        self.device = None
        self.port = port
        self.receive_callback = receive_callback
        self.node_id = None
    
    def connect(self):
        """
        Connect to the Meshtastic device.
        
        Returns:
            bool: True if connected successfully, False otherwise.
        """
        try:
            if self.port:
                self.device = meshtastic.serial_interface.SerialInterface(
                    devPath=self.port
                )
            else:
                # Auto-detect
                self.device = meshtastic.serial_interface.SerialInterface()
            
            # Get device info
            self.node_id = self.device.myInfo.my_node_num
            print(f"Connected to Meshtastic device. Node ID: {self.node_id}")
            
            # Subscribe to receive messages using pubsub if callback provided
            if self.receive_callback:
                pub.subscribe(self._on_message_received, "meshtastic.receive")
            
            return True
        except Exception as e:
            print(f"Failed to connect to Meshtastic device: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the Meshtastic device."""
        if self.receive_callback:
            pub.unsubscribe(self._on_message_received, "meshtastic.receive")
        if self.device:
            self.device.close()
            print("Disconnected from Meshtastic device")
    
    def send_direct_message(self, to_id, message):
        """
        Send a direct message to a specific node.
        
        Args:
            to_id (int or str): Destination node ID
            message (str): Message to send.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        try:
            if not self.device:
                print("Device not connected")
                return False
            
            # Send as direct message
            self.device.sendText(
                message,
                destinationId=to_id,
                wantAck=False
            )
            return True
        except Exception as e:
            print(f"Failed to send direct message: {e}")
            return False
    
    def send_channel_message(self, channel, message):
        """
        Send a message to a channel.
        
        Args:
            message (str): Message to send.
            channel (int): Channel number (default: 0)
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        try:
            if not self.device:
                print("Device not connected")
                return False
            
            # Send to channel (^all means broadcast to all in channel)
            self.device.sendText(
                message,
                destinationId='^all',
                wantAck=False,
                channelIndex=channel
            )
            return True
        except Exception as e:
            print(f"Failed to send channel message: {e}")
            return False
    
    def _on_message_received(self, packet, interface=None):
        """
        Internal callback for received messages using pubsub.
        
        Args:
            packet (dict): Received message packet.
            interface: The meshtastic interface (optional, passed by pubsub).
        """
        if self.receive_callback:
            self.receive_callback(packet)
    
    def get_node_list(self):
        """
        Get list of nodes visible on the network.
        
        Returns:
            list: List of node dictionaries.
        """
        try:
            if not self.device:
                print("Device not connected")
                return []
            
            nodes = self.device.nodes.values()
            return list(nodes)
        except Exception as e:
            print(f"Failed to get node list: {e}")
            return []
    
    def get_device_info(self):
        """
        Get information about the connected device.
        
        Returns:
            dict: Device information.
        """
        try:
            if not self.device:
                print("Device not connected")
                return {}
            
            return {
                "node_id": self.node_id,
                "node_num": getattr(self.device.myInfo, 'my_node_num', None),
                "firmware_version": getattr(self.device.myInfo, 'firmware_version', 'Unknown'),
                "hw_model": getattr(self.device.myInfo, 'hw_model', 'Unknown'),
                "has_wifi": getattr(self.device.myInfo, 'has_wifi', False),
                "has_bluetooth": getattr(self.device.myInfo, 'has_bluetooth', False),
            }
        except Exception as e:
            print(f"Failed to get device info: {e}")
            return {}
    
    def is_connected(self):
        """Check if device is connected."""
        return self.device is not None
    
    def reboot(self):
        """
        Reboot the Meshtastic device.
        
        Returns:
            bool: True if reboot command sent successfully, False otherwise.
        """
        try:
            if not self.device:
                print("Device not connected")
                return False
            
            self.device.localNode.reboot()
            print("Reboot command sent to device")
            return True
        except Exception as e:
            print(f"Failed to reboot device: {e}")
            return False


if __name__ == "__main__":
    def on_message(packet):
        """Example callback for received messages."""
        print(f"Message received: {packet}")
    
    # Create client
    client = MeshtasticClient(port="COM4", receive_callback=on_message)
    
    # Connect
    if client.connect():
        
        '''
        print("\nDevice Info:")
        print(client.get_device_info())
        '''
                
        '''
        node_list = client.get_node_list()
        print("\nNode List:")
        for node in node_list:
            print(node)
        '''
        
        # Send a test message to channel 0
        client.send_channel_message(channel=1, message="Sorry for QRM. Testing...")
        #client.send_direct_message(to_id='!da9e723c', message="Hello direct from Sonde LoRa Bridge!")

        # Keep running for a bit to receive messages
        try:
            time.sleep(15)
        except KeyboardInterrupt:
            pass
        
        # reboot device
        #client.reboot()
        time.sleep(15)
        
        # Disconnect
        client.disconnect()

    else:
        print("Failed to connect")