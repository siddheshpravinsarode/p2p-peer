from config import PORT, STORAGE_DIR
from network.server import P2PServer
from network.client import P2PClient
from gui.app_window import MainWindow

def main():
    # 1. Initialize Network Engines
    server = P2PServer(PORT, STORAGE_DIR)
    client = P2PClient(STORAGE_DIR)

    # 2. Start Background Server
    server.start()

    # 3. Launch UI (Injecting dependencies)
    app = MainWindow(STORAGE_DIR, client)

    # Ensure background server socket closes cleanly when window is closed
    def on_closing():
        server.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()