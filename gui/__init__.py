import os

PORT = 8001
CHUNK_SIZE = 4096
STORAGE_DIR = os.path.join(os.getcwd(), "shared_files")

os.makedirs(STORAGE_DIR, exist_ok=True)