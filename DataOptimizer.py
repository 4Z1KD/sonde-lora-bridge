import json
import cbor2


class DataOptimizer:
    """
    Optimizes JSON data for transmission by minimizing keys and values.
    Supports both JSON and CBOR2 encoding formats.
    """
    
    # Combined field configuration with mapping and scaling
    FIELD_CONFIG = {
        "type": {"key": 0, "scale": 1},
        "station": {"key": 1, "scale": 1},
        "callsign": {"key": 2, "scale": 1},
        "latitude": {"key": 3, "scale": 1e5},
        "longitude": {"key": 4, "scale": 1e5},
        "altitude": {"key": 5, "scale": 1},
        "speed": {"key": 6, "scale": 1e2},
        "heading": {"key": 7, "scale": 1e5},
        "time": {"key": 8, "scale": 1},
        "comment": {"key": 9, "scale": 1},
        "model": {"key": 10, "scale": 1},
        "freq": {"key": 11, "scale": 1e3},
        "temp": {"key": 12, "scale": 10},
        "frame": {"key": 13, "scale": 1},
        "humidity": {"key": 14, "scale": 10},
        "pressure": {"key": 15, "scale": 10},
        "sats": {"key": 16, "scale": 1},
        "batt": {"key": 17, "scale": 10},
        "sdr_device_idx": {"key": 18, "scale": 1},
        "vel_v": {"key": 19, "scale": 10},
        "vel_h": {"key": 20, "scale": 10},
        "bt": {"key": 21, "scale": 1},
        "snr": {"key": 22, "scale": 10},
        "subtype": {"key": 23, "scale": 1},
        "manufacturer": {"key": 24, "scale": 1}        
    }
    
    # Reverse mapping: key -> field_name
    REVERSE_KEY_MAPPING = {config["key"]: name for name, config in FIELD_CONFIG.items()}
    
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
            short_key = self.FIELD_CONFIG[key]["key"] if key in self.FIELD_CONFIG else key
            optimized[short_key] = self._minimize_value(value, key)
        
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
    
    def _minimize_value(self, value, field_name=None):
        """
        Minimize values for transmission using per-field scaling factors.
        
        Args:
            value: Value to minimize.
            field_name: Name of the field (used to look up scaling factor).
            
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
            # Apply field-specific scaling factor
            if field_name and field_name in self.FIELD_CONFIG:
                scale = self.FIELD_CONFIG[field_name]["scale"]
            else:
                scale = 1  # No scaling for fields not in FIELD_CONFIG
            return int(value * scale)
        elif isinstance(value, list):
            # Minimize list values
            return [self._minimize_value(v, field_name) for v in value]
        elif isinstance(value, dict):
            # Recursively minimize nested dicts
            return {self.FIELD_CONFIG[k]["key"] if k in self.FIELD_CONFIG else k: self._minimize_value(v, k) 
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
            full_key = self.REVERSE_KEY_MAPPING.get(short_key, short_key)
            decoded[full_key] = self._restore_value(value, full_key)
        return decoded
    
    def _restore_value(self, value, field_name=None):
        """
        Restore values from optimized format using per-field scaling factors.
        
        Args:
            value: Value to restore.
            field_name: Name of the field (used to look up scaling factor).
            
        Returns:
            Restored value.
        """
        if isinstance(value, int):
            # Restore using field-specific scaling factor
            if field_name and field_name in self.FIELD_CONFIG:
                scale = self.FIELD_CONFIG[field_name]["scale"]
                val = value / scale if scale != 0 else value
                return val if scale != 1 else int(val)
            else:
                return value  # No scaling to remove
        elif isinstance(value, list):
            return [self._restore_value(v, field_name) for v in value]
        elif isinstance(value, dict):
            return {self.REVERSE_KEY_MAPPING.get(k, k): self._restore_value(v, self.REVERSE_KEY_MAPPING.get(k, k)) 
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
    "speed": 120.4, 
    "heading": -9999.0, 
    "time": "17:39:04", 
    "comment": "Radiosonde", 
    "model": "IMET", 
    "freq": "403.9970 MHz", 
    "temp": -5.1, 
    "frame": 1715, 
    "humidity": 4.1, 
    "pressure": 590.5, 
    "sats": 12, 
    "batt": 5.2, 
    "sdr_device_idx": "00000001", 
    "vel_v": 30.4, 
    "vel_h": -4.1,
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

