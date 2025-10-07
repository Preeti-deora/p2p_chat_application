#!/usr/bin/env python3
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple

from net.peer_conn import PeerConn
from storage import Storage


class ChatWindow(tk.Toplevel):
    """
    Modern WhatsApp-like chat interface:
    - Clean header with contact info and status
    - Modern message bubbles with proper styling
    - Smooth scrolling and modern input area
    """
    def __init__(
        self,
        master,
        title: str = "Chat",
        adopt: Optional[Tuple[object, tuple]] = None,
        connect_to: Optional[Tuple[str, int]] = None,
        peer_name: Optional[str] = None,
        storage: Optional[Storage] = None,
    ):
        super().__init__(master)
        self.title(f"Chat with {peer_name or 'Peer'}")
        self.geometry("700x750")
        self.minsize(600, 500)
        
        # Beautiful pastel color scheme
        self.colors = {
            'primary': '#A8E6CF',       # Soft mint green
            'primary_dark': '#7FDBCA',  # Deeper mint
            'secondary': '#FFD3A5',     # Warm peach
            'background': '#FFF8F3',    # Cream background
            'surface': '#FFFFFF',       # Pure white surface
            'text_primary': '#4A5568',  # Soft dark gray
            'text_secondary': '#718096', # Medium gray
            'accent': '#B8E6B8',        # Light green accent
            'success': '#68D391',       # Success green
            'danger': '#FC8181',        # Soft red
            'border': '#E2E8F0',        # Light border
            'hover': '#F0FFF4',         # Very light green hover
            'shadow': '#E2E8F0',        # Subtle shadow
            'my_bubble': '#FFD3A5',     # My message bubble (peach)
            'peer_bubble': '#FFFFFF',   # Peer message bubble (white)
            'chat_bg': '#FFF8F3',       # Chat background (cream)
            'gradient_start': '#FFF8F3', # Gradient start
            'gradient_end': '#F7FAFC'    # Gradient end
        }

        self.storage = storage or Storage()
        self.peer_name = peer_name or "Peer"
        self.peer_ip: Optional[str] = None
        self.peer_port: Optional[int] = None
        self.friend_key: Optional[str] = None

        # Configure window
        self.configure(bg=self.colors['background'])

        # ---- Beautiful Pastel Header ----
        header_frame = tk.Frame(self, bg=self.colors['primary'], height=90)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(self, bg=self.colors['shadow'], height=2)
        shadow_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Header content
        header_content = tk.Frame(header_frame, bg=self.colors['primary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Beautiful contact avatar
        avatar_frame = tk.Frame(header_content, bg=self.colors['secondary'], width=55, height=55)
        avatar_frame.pack(side=tk.LEFT)
        avatar_frame.pack_propagate(False)
        
        initial = self.peer_name[0].upper() if self.peer_name else "?"
        avatar_label = tk.Label(avatar_frame, text=initial, 
                               font=("Segoe UI", 18, "bold"),
                               bg=self.colors['secondary'], fg=self.colors['text_primary'])
        avatar_label.pack(expand=True)
        
        # Contact info with better styling
        contact_info = tk.Frame(header_content, bg=self.colors['primary'])
        contact_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=18)
        
        name_label = tk.Label(contact_info, text=self.peer_name, 
                             font=("Segoe UI", 18, "bold"),
                             bg=self.colors['primary'], fg=self.colors['text_primary'])
        name_label.pack(anchor="w", pady=(0, 2))
        
        self.status_var = tk.StringVar(value="connecting…")
        status_label = tk.Label(contact_info, textvariable=self.status_var, 
                               font=("Segoe UI", 12),
                               bg=self.colors['primary'], fg=self.colors['text_secondary'])
        status_label.pack(anchor="w")

        # ---- Modern Chat Area ----
        chat_container = tk.Frame(self, bg=self.colors['chat_bg'])
        chat_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Scrollable message area
        self.canvas = tk.Canvas(chat_container, bg=self.colors['chat_bg'], highlightthickness=0)
        vs = tk.Scrollbar(chat_container, orient="vertical", command=self.canvas.yview, 
                         bg=self.colors['chat_bg'], troughcolor=self.colors['chat_bg'])
        self.canvas.configure(yscrollcommand=vs.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vs.pack(side=tk.RIGHT, fill=tk.Y)

        self.msg_frame = tk.Frame(self.canvas, bg=self.colors['chat_bg'])
        self.canvas_win = self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.msg_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # ---- Beautiful Pastel Input Area ----
        input_container = tk.Frame(self, bg=self.colors['surface'], height=85)
        input_container.pack(side=tk.BOTTOM, fill=tk.X)
        input_container.pack_propagate(False)
        
        input_frame = tk.Frame(input_container, bg=self.colors['surface'])
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        self.msg_var = tk.StringVar()
        self.entry = tk.Entry(
            input_frame, textvariable=self.msg_var, relief="flat",
            bg=self.colors['background'], fg=self.colors['text_primary'], 
            insertbackground=self.colors['text_primary'],
            font=("Segoe UI", 13), bd=2, highlightthickness=2,
            highlightcolor=self.colors['accent'], highlightbackground=self.colors['border']
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), ipady=14)

        # bind Return; make sure we return 'break' so nothing else fires
        self.entry.bind("<Return>", self.on_send)

        send_btn = tk.Button(
            input_frame, text="➤", font=("Segoe UI", 16, "bold"),
            bg=self.colors['secondary'], fg=self.colors['text_primary'], 
            activebackground=self.colors['primary_dark'],
            activeforeground=self.colors['text_primary'], 
            relief="flat", bd=2, padx=22, pady=14, cursor="hand2",
            command=self.on_send, highlightthickness=0
        )
        send_btn.pack(side=tk.RIGHT)


        # ---- Networking ----
        self.conn = PeerConn(self._ingest_line)
        self.after(80, self._poll_recv)

        if adopt:
            sock, addr = adopt
            # record peer ip/port from incoming
            self.peer_ip, self.peer_port = addr[0], addr[1]
            self.peer_name = self.peer_name or f"{self.peer_ip}"
            self.friend_key = self.storage.upsert_friend(self.peer_name, self.peer_ip, self.peer_port)
            self.conn.adopt(sock, addr)
            self.status_var.set("🟢 Online")
        elif connect_to:
            self.peer_ip, self.peer_port = connect_to
            self.friend_key = self.storage.upsert_friend(self.peer_name or self.peer_ip, self.peer_ip, self.peer_port)
            ok = self.conn.connect(self.peer_ip, self.peer_port)
            self.status_var.set("🟢 Online" if ok else "🔴 Offline")
            if not ok:
                self._system_banner("❌ Could not connect to user", error=True)
        else:
            self.status_var.set("🔴 Offline")
            self._system_banner("❌ No connection information", error=True)

        # Load recent history
        if self.friend_key:
             for rec in self.storage.get_messages(self.friend_key, limit=100):
                side = "right" if rec["dir"] == "out" else "left"
                self._bubble(rec["msg"], side)
                self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- layout helpers ----------
    def _on_frame_configure(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._scroll_to_end()

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_win, width=e.width)

    def _scroll_to_end(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ---------- Modern UI builders ----------
    def _bubble(self, text: str, side: str):
        # Message container
        message_row = tk.Frame(self.msg_frame, bg=self.colors['chat_bg'])
        message_row.pack(fill=tk.X, padx=15, pady=3)

        # Message bubble container
        bubble_container = tk.Frame(message_row, bg=self.colors['chat_bg'])
        
        if side == "left":
            # Peer message (left side)
            bubble_container.pack(side=tk.LEFT, anchor="w")
            bubble_bg = self.colors['peer_bubble']
            text_color = self.colors['text_primary']
            bubble_anchor = "w"
            max_width = 400
        else:
            # My message (right side)
            bubble_container.pack(side=tk.RIGHT, anchor="e")
            bubble_bg = self.colors['my_bubble']
            text_color = self.colors['text_primary']
            bubble_anchor = "e"
            max_width = 400

        # Create bubble with rounded corners effect
        bubble_frame = tk.Frame(bubble_container, bg=bubble_bg, relief="flat", bd=1)
        bubble_frame.pack(anchor=bubble_anchor, padx=5)

        # Message text
        message_label = tk.Label(
            bubble_frame, text=text, bg=bubble_bg, fg=text_color, 
            justify="left", wraplength=max_width,
            padx=15, pady=12, font=("Segoe UI", 11),
            anchor="w"
        )
        message_label.pack()

        # Add some spacing between messages
        spacer = tk.Frame(self.msg_frame, bg=self.colors['chat_bg'], height=5)
        spacer.pack(fill=tk.X)

    def _system_banner(self, text: str, error: bool = False):
        # System message container
        system_row = tk.Frame(self.msg_frame, bg=self.colors['chat_bg'])
        system_row.pack(fill=tk.X, padx=20, pady=5)
        
        # System message banner
        banner_bg = "#FFF3CD" if not error else "#F8D7DA"
        banner_fg = "#856404" if not error else "#721C24"
        
        system_pill = tk.Label(
            system_row, text=text,
            bg=banner_bg, fg=banner_fg, 
            font=("Segoe UI", 9, "bold"),
            padx=12, pady=6, relief="flat"
        )
        system_pill.pack()

    # ---------- network → UI ----------
    def _ingest_line(self, line: str):
        if line.startswith("[system]"):
            self._system_banner(line)
        elif line.startswith("[error]"):
            self._system_banner(line, error=True)
        else:
            self._bubble(line, side="left")
            # persist incoming
            if self.friend_key:
                self.storage.add_message(self.friend_key, "in", line)


    def _poll_recv(self):
        self.conn.poll_recv()
        self.after(80, self._poll_recv)

    # ---------- send ----------
    def on_send(self, event=None):
        msg = self.msg_var.get().strip()
        if not msg:
            return "break" if event else None

        self.conn.send(msg)
        self._bubble(msg, side="right")
        if self.friend_key:
            self.storage.add_message(self.friend_key, "out", msg)

        self.msg_var.set("")
        try:
            self.entry.delete(0, tk.END)
        except Exception:
            pass
        self._scroll_to_end()
        return "break" if event else None


    # ---------- close ----------
    def _on_close(self):
        try:
            self.conn.close()
        finally:
            self.destroy()
