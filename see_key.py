import os
base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of your script
key_path = os.path.join(base_dir, 'secret.key')

with open(key_path, 'rb') as f:
    key = f.read()
    print("Key bytes:", key)
    print("Key string:", key.decode() if hasattr(key, 'decode') else key)