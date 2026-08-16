import os
import json
import socket
import threading
import hashlib
import time
from config import CHUNK_SIZE

class P2PClient:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir

    def download(self, address: str, filename: str, progress_cb, status_cb):
        """Connects to remote peer and streams file with SHA-256 validation."""
        def _task():
            client = None
            try:
                address_clean = address.strip()
                if ":" not in address_clean:
                    status_cb("Invalid address format. Use host:port (e.g., 192.168.1.5:8001)", False)
                    return

                parts = address_clean.split(":")
                host = parts[0].strip()
                port = int(parts[1].strip())

                status_cb(f"Connecting to peer {host}:{port}...", True)
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(10.0)
                client.connect((host, port))

                # Send GET command
                clean_filename = os.path.basename(filename.strip())
                client.sendall(f"GET:{clean_filename}".encode('utf-8'))

                response = client.recv(1024).decode('utf-8').strip()
                if not response.startswith("EXISTS"):
                    status_cb("[-] File not found on remote peer.", False)
                    return

                res_parts = response.split("|")
                if len(res_parts) < 3:
                    status_cb("[-] Invalid protocol response from peer.", False)
                    return

                total_bytes = int(res_parts[1])
                expected_hash = res_parts[2]

                client.sendall(b"READY")
                client.settimeout(15.0) # 15s timeout between chunks

                os.makedirs(self.storage_dir, exist_ok=True)
                out_path = os.path.join(self.storage_dir, clean_filename)
                
                # Handle file collision if destination file already exists
                if os.path.exists(out_path):
                    base, ext = os.path.splitext(clean_filename)
                    out_path = os.path.join(self.storage_dir, f"{base}_downloaded{ext}")

                sha256 = hashlib.sha256()
                received = 0
                start_time = time.time()

                with open(out_path, 'wb') as f:
                    while received < total_bytes:
                        bytes_to_read = min(CHUNK_SIZE, total_bytes - received)
                        chunk = client.recv(bytes_to_read)
                        if not chunk:
                            break
                        f.write(chunk)
                        sha256.update(chunk)
                        received += len(chunk)

                        if total_bytes > 0:
                            ratio = received / total_bytes
                            elapsed = time.time() - start_time
                            speed_kb = (received / 1024) / elapsed if elapsed > 0 else 0
                            progress_cb(ratio, received, total_bytes, speed_kb)

                computed_hash = sha256.hexdigest()
                if computed_hash == expected_hash:
                    status_cb(f"[SUCCESS] Complete & Verified SHA-256!\nSaved to: {out_path}", True)
                else:
                    if os.path.exists(out_path):
                        os.remove(out_path)
                    status_cb("[FAILED] Integrity check failed! Hash mismatch. Partial file removed.", False)

            except socket.timeout:
                status_cb("[-] Connection timed out while communicating with peer.", False)
            except ConnectionRefusedError:
                status_cb("[-] Connection refused. Ensure peer server is running and port is open.", False)
            except Exception as e:
                status_cb(f"[-] Download error: {e}", False)
            finally:
                if client:
                    try:
                        client.close()
                    except Exception:
                        pass

        threading.Thread(target=_task, daemon=True).start()

    def fetch_remote_file_list(self, address: str, callback):
        """Fetches the list of shared files hosted on a remote peer."""
        def _task():
            client = None
            try:
                address_clean = address.strip()
                if ":" not in address_clean:
                    callback(False, "Invalid address format. Use host:port")
                    return

                parts = address_clean.split(":")
                host = parts[0].strip()
                port = int(parts[1].strip())

                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5.0)
                client.connect((host, port))
                client.sendall(b"LIST")

                raw_resp = client.recv(4096).decode('utf-8').strip()
                if raw_resp.startswith("LIST_OK|"):
                    json_str = raw_resp[8:]
                    file_list = json.loads(json_str)
                    callback(True, file_list)
                else:
                    callback(False, "Peer does not support file listing.")
            except Exception as e:
                callback(False, f"Could not connect to peer: {e}")
            finally:
                if client:
                    try:
                        client.close()
                    except Exception:
                        pass

        threading.Thread(target=_task, daemon=True).start()