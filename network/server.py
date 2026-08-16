import os
import json
import socket
import threading
from config import CHUNK_SIZE
from crypto import calculate_sha256

class P2PServer:
    def __init__(self, port: int, storage_dir: str):
        self.port = port
        self.storage_dir = storage_dir
        self.running = False
        self.server_socket = None

    def start(self):
        """Starts the P2P server in a background thread."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            self.running = True
            threading.Thread(target=self._listen, daemon=True).start()
            print(f"[+] P2P Server listening on port {self.port}")
        except Exception as e:
            print(f"[-] Failed to start P2P Server: {e}")

    def stop(self):
        """Stops the server gracefully."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _listen(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()
            except Exception:
                if not self.running:
                    break

    def _handle(self, conn: socket.socket, addr):
        try:
            conn.settimeout(10.0)
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                return

            # Protocol Command 1: LIST - returns all hosted files in storage_dir
            if data == "LIST":
                file_list = []
                if os.path.exists(self.storage_dir):
                    for fname in os.listdir(self.storage_dir):
                        fpath = os.path.join(self.storage_dir, fname)
                        if os.path.isfile(fpath):
                            size = os.path.getsize(fpath)
                            file_list.append({"name": fname, "size": size})
                response = "LIST_OK|" + json.dumps(file_list)
                conn.sendall(response.encode('utf-8'))
                return

            # Protocol Command 2: GET:<filename> or <filename>
            filename = data[4:].strip() if data.startswith("GET:") else data
            # Prevent directory traversal attacks
            filename = os.path.basename(filename)
            filepath = os.path.join(self.storage_dir, filename)

            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_hash = calculate_sha256(filepath)

                conn.sendall(f"EXISTS|{file_size}|{file_hash}".encode('utf-8'))
                
                # Wait for client READY signal
                ready_signal = conn.recv(1024).decode('utf-8').strip()
                if ready_signal != "READY":
                    return

                conn.settimeout(None) # Remove timeout for large file transfer
                with open(filepath, 'rb') as f:
                    while chunk := f.read(CHUNK_SIZE):
                        conn.sendall(chunk)
            else:
                conn.sendall(b"NOT_FOUND")
        except Exception as e:
            print(f"[-] Server error handling client {addr}: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass