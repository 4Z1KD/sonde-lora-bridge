from DataOptimizer import DataOptimizer
import json

# Create optimizer instance
optimizer = DataOptimizer()

print("=== Optimizer Tester ===")
print("Enter a hex string (CBOR2 encoded data) to decode back to JSON")
print("Or enter 'quit' to exit\n")

while True:
    hex_input = input("Enter hex string (or 'quit'): ").strip()
    
    if hex_input.lower() == 'quit':
        print("Exiting...")
        break
    
    if not hex_input:
        print("Please enter a valid hex string\n")
        continue
    
    try:
        # Convert hex string to bytes
        cbor_bytes = bytes.fromhex(hex_input)
        
        # Decode from CBOR2 back to JSON
        decoded = optimizer.from_cbor2(cbor_bytes)
        
        print("\nDecoded JSON:")
        print(json.dumps(decoded, indent=2))
        print()
    except ValueError:
        print("Invalid hex string. Please enter a valid hexadecimal string.\n")
    except Exception as e:
        print(f"Error decoding: {e}\n")
