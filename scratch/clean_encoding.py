import sys

def clean_file(path):
    try:
        # Try reading with cp1252 or latin-1 which handles all bytes
        with open(path, 'rb') as f:
            content = f.read()
        
        # Try to decode as utf-8 first to see where it fails
        try:
            decoded = content.decode('utf-8')
            print("File is already UTF-8")
        except UnicodeDecodeError:
            print("File is NOT UTF-8, cleaning...")
            # Decode using cp874 (Thai Windows) or latin-1
            try:
                decoded = content.decode('cp874')
                print("Decoded with cp874")
            except:
                decoded = content.decode('latin-1')
                print("Decoded with latin-1")

        # Add UTF-8 header and write back
        header = "# -*- coding: utf-8 -*-\n"
        if not decoded.startswith("# -*- coding: utf-8 -*-"):
            decoded = header + decoded
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(decoded)
        print("Done cleaning")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_file(sys.argv[1])
