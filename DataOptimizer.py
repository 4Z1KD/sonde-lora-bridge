import json
import cbor2


class DataOptimizer:
    """
    Optimizes JSON data for transmission by minimizing keys and values.
    Supports both JSON and CBOR2 encoding formats.
    """
    
    # Mapping of full field names to shortened keys (as integers)
    FIELD_MAPPING = {
    "type": 0, 
    "station": 1,
    "callsign": 2,
    "latitude": 3,
    "longitude": 4,
    "altitude": 5, 
    "speed": 6, 
    "heading": 7, 
    "time": 8, 
    "comment": 9,
    "model": 10,
    "freq": 11,
    "temp": 12, 
    "frame": 13, 
    "humidity": 14, 
    "pressure": 15, 
    "sats": 16, 
    "batt": 17, 
    "sdr_device_idx": 18, 
    "vel_v": 19, 
    "vel_h": 20,
    "bt": 21, 
    "snr": 22,
    "subtype": 23
    }
    
    # Reverse mapping for decoding
    REVERSE_MAPPING = {v: k for k, v in FIELD_MAPPING.items()}
    
    def __init__(self):
        """Initialize the data optimizer."""
        pass
    
    def optimize_json(self, data):
        """
        Optimize JSON data by minimizing keys.
        
        Args:
            data (dict or str): JSON data to optimize. Can be dict or JSON string.
            
        Returns:
            dict: Optimized data with shortened keys.
        """
        # Parse if string
        if isinstance(data, str):
            data = json.loads(data)
        
        optimized = {}
        for key, value in data.items():
            short_key = self.FIELD_MAPPING.get(key, key)
            optimized[short_key] = self._minimize_value(value)
        
        return optimized
    
    def to_json_string(self, data):
        """
        Convert optimized data to compact JSON string.
        
        Args:
            data (dict): Data to convert.
            
        Returns:
            str: Compact JSON string without whitespace.
        """
        optimized = self.optimize_json(data)
        return json.dumps(optimized, separators=(',', ':'), ensure_ascii=False)
    
    def to_cbor2(self, data):
        """
        Convert optimized data to CBOR2 binary format.
        
        Args:
            data (dict): Data to convert.
            
        Returns:
            bytes: CBOR2 encoded data.
        """
        optimized = self.optimize_json(data)
        return cbor2.dumps(optimized)
    
    def from_cbor2(self, cbor_bytes):
        """
        Deserialize CBOR2 binary data back to JSON with full field names.
        
        Args:
            cbor_bytes (bytes): CBOR2 encoded data (from HEX).
            
        Returns:
            dict: Decoded data with full field names restored.
        """

        optimized = cbor2.loads(cbor_bytes)
        return self.decode_json(optimized)
    
    def _minimize_value(self, value):
        """
        Minimize values for transmission.
        
        Args:
            value: Value to minimize.
            
        Returns:
            Minimized value.
        """
        if isinstance(value, bool):
            # Convert booleans to 0/1
            return 1 if value else 0
        elif isinstance(value, str):
            # Keep strings as-is
            return value
        elif isinstance(value, (int, float)):
            # Round floats to reasonable precision
            return int(value * 100000)
        elif isinstance(value, list):
            # Minimize list values
            return [self._minimize_value(v) for v in value]
        elif isinstance(value, dict):
            # Recursively minimize nested dicts
            return {self.FIELD_MAPPING.get(k, k): self._minimize_value(v) 
                    for k, v in value.items()}
        return value
    
    def decode_json(self, optimized_data):
        """
        Decode optimized JSON back to full field names.
        
        Args:
            optimized_data (dict): Optimized data with shortened keys.
            
        Returns:
            dict: Data with full field names restored.
        """
        decoded = {}
        for short_key, value in optimized_data.items():
            full_key = self.REVERSE_MAPPING.get(short_key, short_key)
            decoded[full_key] = self._restore_value(value)
        return decoded
    
    def _restore_value(self, value):
        """
        Restore values from optimized format.
        
        Args:
            value: Value to restore.
            
        Returns:
            Restored value.
        """
        if isinstance(value, int):
            if value == 0:
                # Ambiguous: could be boolean or number, keep as int
                return value
            else:
                return value/100000
        elif isinstance(value, list):
            return [self._restore_value(v) for v in value]
        elif isinstance(value, dict):
            return {self.REVERSE_MAPPING.get(k, k): self._restore_value(v) 
                    for k, v in value.items()}
        return value


if __name__ == "__main__":
    optimizer = DataOptimizer()
    
    real_packet = {
    "type": "PAYLOAD_SUMMARY", 
    "station": "4Z1KD", 
    "callsign": "IMET-8120B666", 
    "latitude": 31.87804, 
    "longitude": 34.74142, 
    "altitude": 4523, 
    "speed": -35996.4, 
    "heading": -9999.0, 
    "time": "17:39:04", 
    "comment": "Radiosonde", 
    "model": "IMET", 
    "freq": "403.9970 MHz", 
    "temp": -5.18, 
    "frame": 1715, 
    "humidity": 4.1, 
    "pressure": 590.5, 
    "sats": 12, 
    "batt": 5.2, 
    "sdr_device_idx": "00000001", 
    "vel_v": -9999.0, 
    "vel_h": -9999.0,
    }
    
    # Optimize to JSON
    '''
    optimized_json = optimizer.to_json_string(real_packet)
    print(f"Original size: {len(json.dumps(real_packet))} bytes")
    print(f"Optimized JSON: {optimized_json}")
    print(f"Optimized JSON size: {len(optimized_json)} bytes")
    print()
    '''
    
    # Optimize to CBOR2
    cbor_data = optimizer.to_cbor2(real_packet)
    print(f"CBOR2 size: {len(cbor_data)} bytes")
    cbor_hex = cbor_data.hex()
    print(f"CBOR2 (hex): {cbor_hex}")


    # CBOR2 back to JSON
    cbor_bytes = bytes.fromhex(cbor_hex)
    decoded_data = optimizer.from_cbor2(cbor_bytes)
    print("Decoded from CBOR2:")
    print(json.dumps(decoded_data, indent=2))

