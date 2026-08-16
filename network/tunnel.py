import socket
import threading
from pyngrok import ngrok

def get_local_ip() -> str:
    """Discovers the active local LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_peer_address(port: int) -> str:
    """Returns formatted IP:PORT string for sharing with peers on local network."""
    return f"{get_local_ip()}:{port}"

def start_tunnel(port: int, on_ready_callback):
    """Spawns an Ngrok tunnel in the background for global WAN sharing."""
    def _setup():
        try:
            tunnel = ngrok.connect(port, "tcp")
            address = tunnel.public_url.replace("tcp://", "")
            on_ready_callback(address)
        except Exception as e:
            on_ready_callback(f"Tunnel Error: {e}")
            
    threading.Thread(target=_setup, daemon=True).start()
