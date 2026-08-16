import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from crypto import calculate_sha256

class HostPanel(ctk.CTkFrame):
    def __init__(self, master, storage_dir: str):
        super().__init__(master)
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

        self._build_ui()
        self.refresh_hosted_files()

    def _build_ui(self):
        # Header Section
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)

        title_label = ctk.CTkLabel(
            header_frame, 
            text="Shared Storage (Hosting)", 
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(side="left")

        btn_add = ctk.CTkButton(
            header_frame, 
            text="+ Host File", 
            width=110,
            command=self.add_file,
            fg_color="#10B981", 
            hover_color="#059669"
        )
        btn_add.pack(side="right", padx=5)

        btn_refresh = ctk.CTkButton(
            header_frame, 
            text="↻ Refresh", 
            width=90,
            command=self.refresh_hosted_files,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        btn_refresh.pack(side="right", padx=5)

        # Scrollable container for file items
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Hosted Files")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Footer Status Label
        self.lbl_summary = ctk.CTkLabel(
            self, 
            text="0 files hosted", 
            font=("Segoe UI", 11),
            text_color="gray"
        )
        self.lbl_summary.pack(anchor="w", padx=15, pady=5)

    def add_file(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                filename = os.path.basename(path)
                dest = os.path.join(self.storage_dir, filename)
                shutil.copy2(path, dest)
                self.refresh_hosted_files()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to host file: {e}")

    def refresh_hosted_files(self):
        # Clear existing widgets in scroll_frame
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

        files = [f for f in os.listdir(self.storage_dir) if os.path.isfile(os.path.join(self.storage_dir, f))]
        
        if not files:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame, 
                text="No files currently hosted.\nClick '+ Host File' to share files with peers.",
                text_color="gray",
                font=("Segoe UI", 12)
            )
            empty_lbl.pack(pady=30)
            self.lbl_summary.configure(text="0 files hosted")
            return

        total_bytes = 0
        for filename in files:
            filepath = os.path.join(self.storage_dir, filename)
            size = os.path.getsize(filepath)
            total_bytes += size
            file_hash = calculate_sha256(filepath)

            # File Card Frame
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E293B", corner_radius=8)
            card.pack(fill="x", padx=5, pady=5)

            # File info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            name_lbl = ctk.CTkLabel(
                info_frame, 
                text=filename, 
                font=("Segoe UI", 13, "bold"),
                anchor="w"
            )
            name_lbl.pack(anchor="w")

            size_str = self._format_size(size)
            meta_lbl = ctk.CTkLabel(
                info_frame, 
                text=f"Size: {size_str}  |  SHA-256: {file_hash[:16]}...", 
                font=("Segoe UI", 11),
                text_color="#94A3B8",
                anchor="w"
            )
            meta_lbl.pack(anchor="w")

            # Actions
            btn_copy_hash = ctk.CTkButton(
                card,
                text="Copy SHA-256",
                width=100,
                height=28,
                fg_color="#475569",
                hover_color="#334155",
                command=lambda h=file_hash: self._copy_to_clipboard(h, "SHA-256 Hash copied to clipboard!")
            )
            btn_copy_hash.pack(side="right", padx=10, pady=8)

        total_size_str = self._format_size(total_bytes)
        self.lbl_summary.configure(text=f"Hosting {len(files)} file(s) ({total_size_str}) in {self.storage_dir}")

    def _copy_to_clipboard(self, text: str, msg: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", msg)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"