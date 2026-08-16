import os

# Network & File Transfer Settings
PORT = 8001
CHUNK_SIZE = 4096  # 4KB transfer chunks

# Default storage directory for shared and downloaded files
STORAGE_DIR = os.path.join(os.getcwd(), "shared_files")
os.makedirs(STORAGE_DIR, exist_ok=True)