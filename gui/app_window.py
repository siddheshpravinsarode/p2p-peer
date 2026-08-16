import os
import socket
import subprocess
import customtkinter as ctk
from tkinter import messagebox
from config import PORT
from network.tunnel import start_tunnel
from gui.host_panel import HostPanel

def get_local_ip() -> str:
    """Discovers local LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class MainWindow(ctk.CTk):
    def __init__(self, storage_dir: str, client):
        super().__init__()
        self.storage_dir = storage_dir
        self.client = client

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("P2P Secure File Sharing")
        self.geometry("850x650")
        self.minsize(750, 580)

        self.local_address = f"{get_local_ip()}:{PORT}"
        self.current_address = self.local_address

        self._build_header()
        self._build_tabs()

        # Bring window to foreground on screen
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.focus_force()

        # Schedule Ngrok tunnel setup after window is rendered
        self.after(500, self._init_ngrok_tunnel)

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#0F172A", height=75, corner_radius=0)
        header_frame.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(
            header_frame, 
            text="⚡ P2P File Share", 
            font=("Segoe UI", 20, "bold"),
            text_color="#38BDF8"
        )
        title_lbl.pack(side="left", padx=20, pady=15)

        # Status badge
        self.status_lbl = ctk.CTkLabel(
            header_frame,
            text="● Server Active",
            font=("Segoe UI", 12, "bold"),
            text_color="#10B981"
        )
        self.status_lbl.pack(side="right", padx=(5, 20), pady=15)

        # Address button (displays local LAN IP or Ngrok public tunnel)
        self.btn_address = ctk.CTkButton(
            header_frame,
            text=f"Address: {self.current_address}",
            font=("Segoe UI", 11, "bold"),
            fg_color="#1E293B",
            hover_color="#334155",
            border_width=1,
            border_color="#38BDF8",
            command=self._copy_address
        )
        self.btn_address.pack(side="right", padx=5, pady=15)

    def _init_ngrok_tunnel(self):
        self.btn_address.configure(text=f"Connecting Tunnel... (LAN: {self.local_address})")

        def _on_ready(address):
            def _update():
                if address and not address.startswith("Tunnel Error"):
                    self.current_address = address
                    self.btn_address.configure(
                        text=f"Public Address: {address}",
                        fg_color="#065F46",
                        border_color="#10B981"
                    )
                    self.status_lbl.configure(text="● Public Tunnel Active", text_color="#10B981")
                    self._log(f"[Tunnel] Public Ngrok Tunnel online: {address}")
                else:
                    self.current_address = self.local_address
                    self.btn_address.configure(
                        text=f"LAN Address: {self.local_address}",
                        fg_color="#1E293B",
                        border_color="#38BDF8"
                    )
                    err_msg = address if address else "Unknown error"
                    self._log(f"[Tunnel Info] Using Local Address ({self.local_address}). Ngrok info: {err_msg}")

            self.after(0, _update)

        start_tunnel(PORT, _on_ready)

    def _copy_address(self):
        self.clipboard_clear()
        self.clipboard_append(self.current_address)
        messagebox.showinfo("Address Copied", f"Shareable address '{self.current_address}' copied to clipboard!\nProvide this address to your peer.")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_host = self.tabview.add("Host Files")
        self.tab_download = self.tabview.add("Download File")
        self.tab_storage = self.tabview.add("Storage Explorer")

        # Tab 1: Host Files Panel
        self.host_panel = HostPanel(self.tab_host, self.storage_dir)
        self.host_panel.pack(fill="both", expand=True)

        # Tab 2: Download File Panel
        self._build_download_tab()

        # Tab 3: Storage Explorer Panel
        self._build_storage_tab()

    def _build_download_tab(self):
        dl_frame = ctk.CTkFrame(self.tab_download, fg_color="transparent")
        dl_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Connection inputs frame
        conn_frame = ctk.CTkFrame(dl_frame, fg_color="#1E293B", corner_radius=8)
        conn_frame.pack(fill="x", pady=(0, 15), padx=5)

        ctk.CTkLabel(
            conn_frame, 
            text="Peer Connection & Request", 
            font=("Segoe UI", 14, "bold"),
            text_color="#F8FAFC"
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 5))

        # Peer Address Entry
        ctk.CTkLabel(conn_frame, text="Peer Address (IP:Port or Ngrok URL):", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.entry_peer_addr = ctk.CTkEntry(conn_frame, placeholder_text="e.g. 192.168.1.50:8001 or 0.tcp.ngrok.io:12345", width=280)
        self.entry_peer_addr.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.entry_peer_addr.insert(0, f"127.0.0.1:{PORT}")

        btn_fetch = ctk.CTkButton(
            conn_frame,
            text="Fetch Peer Files",
            width=130,
            fg_color="#0EA5E9",
            hover_color="#0284C7",
            command=self._fetch_remote_files
        )
        btn_fetch.grid(row=1, column=2, padx=15, pady=5)

        # Filename Entry / Selector
        ctk.CTkLabel(conn_frame, text="Filename to Request:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=15, pady=(5, 15))
        self.entry_filename = ctk.CTkEntry(conn_frame, placeholder_text="e.g. sample.pdf", width=280)
        self.entry_filename.grid(row=2, column=1, sticky="w", padx=5, pady=(5, 15))

        self.btn_download = ctk.CTkButton(
            conn_frame,
            text="Download File",
            width=130,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._start_download
        )
        self.btn_download.grid(row=2, column=2, padx=15, pady=(5, 15))

        # Remote Files Info Label
        self.lbl_remote_info = ctk.CTkLabel(conn_frame, text="", font=("Segoe UI", 11), text_color="#38BDF8")
        self.lbl_remote_info.grid(row=3, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 10))

        # Transfer Progress Section
        progress_card = ctk.CTkFrame(dl_frame, fg_color="#1E293B", corner_radius=8)
        progress_card.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(
            progress_card, 
            text="Transfer Status & Progress", 
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_card, orientation="horizontal")
        self.progress_bar.pack(fill="x", padx=15, pady=10)
        self.progress_bar.set(0)

        self.lbl_progress_meta = ctk.CTkLabel(
            progress_card, 
            text="Idle - Ready to start transfer", 
            font=("Segoe UI", 12),
            text_color="#94A3B8"
        )
        self.lbl_progress_meta.pack(anchor="w", padx=15, pady=(0, 10))

        # Log output textbox
        self.txt_log = ctk.CTkTextbox(dl_frame, height=130, font=("Consolas", 11))
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=10)
        self.txt_log.insert("end", "[System] Ready. Enter peer address (Local IP or Ngrok URL) and filename to download.\n")

    def _fetch_remote_files(self):
        address = self.entry_peer_addr.get().strip()
        if not address:
            messagebox.showwarning("Warning", "Please enter a peer address.")
            return

        self._log(f"[Info] Requesting file list from peer '{address}'...")
        self.lbl_remote_info.configure(text="Fetching remote files...")

        def _cb(success, result):
            def _update():
                if success:
                    if isinstance(result, list) and len(result) > 0:
                        files_str = ", ".join([f['name'] for f in result])
                        self.lbl_remote_info.configure(text=f"Remote files available ({len(result)}): {files_str}")
                        self._log(f"[Success] Found {len(result)} files on peer.")
                        if result:
                            self.entry_filename.delete(0, "end")
                            self.entry_filename.insert(0, result[0]['name'])
                    else:
                        self.lbl_remote_info.configure(text="Peer has 0 files hosted.")
                        self._log("[Info] Peer has no files in storage.")
                else:
                    self.lbl_remote_info.configure(text=f"Error: {result}")
                    self._log(f"[Error] {result}")
            self.after(0, _update)

        self.client.fetch_remote_file_list(address, _cb)

    def _start_download(self):
        address = self.entry_peer_addr.get().strip()
        filename = self.entry_filename.get().strip()

        if not address or not filename:
            messagebox.showwarning("Warning", "Please provide both Peer Address and Filename.")
            return

        self.btn_download.configure(state="disabled")
        self.progress_bar.set(0)
        self._log(f"[Download] Starting download request for '{filename}' from {address}...")

        def progress_cb(ratio, received, total, speed_kb):
            def _update():
                self.progress_bar.set(ratio)
                pct = int(ratio * 100)
                rec_mb = received / (1024 * 1024)
                tot_mb = total / (1024 * 1024)
                self.lbl_progress_meta.configure(
                    text=f"{pct}% ({rec_mb:.2f} MB / {tot_mb:.2f} MB) - {speed_kb:.1f} KB/s"
                )
            self.after(0, _update)

        def status_cb(msg, success):
            def _update():
                self._log(msg)
                self.lbl_progress_meta.configure(text=msg)
                self.btn_download.configure(state="normal")
                if success:
                    self.progress_bar.set(1.0)
                    self.host_panel.refresh_hosted_files()
                    self._refresh_storage_tab()
            self.after(0, _update)

        self.client.download(address, filename, progress_cb, status_cb)

    def _log(self, text: str):
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")

    def _build_storage_tab(self):
        self.storage_tab_frame = ctk.CTkFrame(self.tab_storage, fg_color="transparent")
        self.storage_tab_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctrl_frame = ctk.CTkFrame(self.storage_tab_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 10))

        lbl_path = ctk.CTkLabel(
            ctrl_frame,
            text=f"Location: {self.storage_dir}",
            font=("Segoe UI", 12),
            text_color="#94A3B8"
        )
        lbl_path.pack(side="left")

        btn_open_folder = ctk.CTkButton(
            ctrl_frame,
            text="📁 Open Folder",
            width=120,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._open_storage_folder
        )
        btn_open_folder.pack(side="right", padx=5)

        btn_refresh_stg = ctk.CTkButton(
            ctrl_frame,
            text="↻ Refresh",
            width=90,
            fg_color="#475569",
            hover_color="#334155",
            command=self._refresh_storage_tab
        )
        btn_refresh_stg.pack(side="right", padx=5)

        self.storage_scroll = ctk.CTkScrollableFrame(self.storage_tab_frame, label_text="Files in Local Storage")
        self.storage_scroll.pack(fill="both", expand=True)

        self._refresh_storage_tab()

    def _open_storage_folder(self):
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            if os.name == 'nt':
                os.startfile(self.storage_dir)
            else:
                subprocess.Popen(['xdg-open', self.storage_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {e}")

    def _refresh_storage_tab(self):
        for child in self.storage_scroll.winfo_children():
            child.destroy()

        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

        files = [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]

        if not files:
            lbl = ctk.CTkLabel(
                self.storage_scroll, 
                text="Storage folder is empty.",
                font=("Segoe UI", 12),
                text_color="gray"
            )
            lbl.pack(pady=20)
            return

        for filename in files:
            filepath = os.path.join(self.storage_dir, filename)
            size_kb = os.path.getsize(filepath) / 1024

            item_frame = ctk.CTkFrame(self.storage_scroll, fg_color="#1E293B")
            item_frame.pack(fill="x", padx=5, pady=4)

            name_lbl = ctk.CTkLabel(item_frame, text=filename, font=("Segoe UI", 12, "bold"))
            name_lbl.pack(side="left", padx=10, pady=8)

            meta_lbl = ctk.CTkLabel(item_frame, text=f"{size_kb:.1f} KB", text_color="#94A3B8", font=("Segoe UI", 11))
            meta_lbl.pack(side="left", padx=10, pady=8)

            btn_open = ctk.CTkButton(
                item_frame,
                text="Open File",
                width=80,
                height=26,
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=lambda p=filepath: self._open_file(p)
            )
            btn_open.pack(side="right", padx=10, pady=8)

    def _open_file(self, filepath: str):
        try:
            if os.name == 'nt':
                os.startfile(filepath)
            else:
                subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open file: {e}")
