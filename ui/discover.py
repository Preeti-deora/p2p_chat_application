#!/usr/bin/env python3
from __future__ import annotations
import queue
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from net.presence import Presence
from net.inbox import InboxServer
from net.global_discovery import GlobalDiscovery
from ui.chat_window import ChatWindow
from storage import Storage


class DiscoverApp(tk.Tk):
    """
    Modern WhatsApp-like main window:
    - Clean header with user info and online status
    - Modern contact list with avatars and status indicators
    - Smooth animations and modern styling
    """
    def __init__(self):
        super().__init__()
        self.title("P2P Chat - WhatsApp Style")
        self.geometry("900x650")
        self.minsize(800, 550)
        
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
            'gradient_start': '#FFF8F3', # Gradient start
            'gradient_end': '#F7FAFC'    # Gradient end
        }
        
        # Configure root window
        self.configure(bg=self.colors['background'])

        self.storage = Storage()

        # --- Beautiful Pastel Header ---
        header_frame = tk.Frame(self, bg=self.colors['primary'], height=90)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(self, bg=self.colors['shadow'], height=2)
        shadow_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Header content
        header_content = tk.Frame(header_frame, bg=self.colors['primary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # App title with better typography
        title_label = tk.Label(header_content, text="💬 P2P Chat", 
                              font=("Segoe UI", 24, "bold"), 
                              bg=self.colors['primary'], fg=self.colors['text_primary'])
        title_label.pack(side=tk.LEFT, anchor="w")
        
        # Subtitle
        subtitle_label = tk.Label(header_content, text="Connect • Chat • Discover", 
                                 font=("Segoe UI", 11), 
                                 bg=self.colors['primary'], fg=self.colors['text_secondary'])
        subtitle_label.pack(side=tk.LEFT, anchor="w", padx=(10, 0), pady=(5, 0))
        
        # User info section with better styling
        user_section = tk.Frame(header_content, bg=self.colors['primary'])
        user_section.pack(side=tk.RIGHT, anchor="e")
        
        # Display name input with rounded appearance
        name_label = tk.Label(user_section, text="👤 Your Name:", 
                             font=("Segoe UI", 11, "bold"), 
                             bg=self.colors['primary'], fg=self.colors['text_primary'])
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.name_var = tk.StringVar(value=f"User-{random.randint(100,999)}")
        name_entry = tk.Entry(user_section, textvariable=self.name_var, width=18,
                             font=("Segoe UI", 11), relief="flat", bd=2,
                             bg=self.colors['surface'], fg=self.colors['text_primary'],
                             highlightthickness=2, highlightcolor=self.colors['accent'],
                             highlightbackground=self.colors['border'])
        name_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=8)
        
        # Online button with better styling
        self.go_btn = tk.Button(user_section, text="🚀 Go Online", 
                               command=self.on_start,
                               font=("Segoe UI", 11, "bold"),
                               bg=self.colors['secondary'], fg=self.colors['text_primary'],
                               activebackground=self.colors['primary_dark'],
                               activeforeground=self.colors['text_primary'],
                               relief="flat", bd=2, padx=25, pady=8,
                               cursor="hand2", highlightthickness=0)
        self.go_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Status indicator with emoji
        self.status_var = tk.StringVar(value="⚪ Offline")
        status_label = tk.Label(user_section, textvariable=self.status_var,
                               font=("Segoe UI", 11, "bold"), 
                               bg=self.colors['primary'], fg=self.colors['text_secondary'])
        status_label.pack(side=tk.RIGHT)

        # --- Modern Content Area ---
        content_frame = tk.Frame(self, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Tab selector with beautiful pastel styling
        tab_frame = tk.Frame(content_frame, bg=self.colors['surface'], height=60)
        tab_frame.pack(fill=tk.X, padx=25, pady=(25, 0))
        tab_frame.pack_propagate(False)
        
        # Tab buttons with improved styling
        self.tab_online = tk.Button(tab_frame, text="🏠 Local Network", 
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.colors['accent'], fg=self.colors['text_primary'],
                                   activebackground=self.colors['primary_dark'],
                                   activeforeground=self.colors['text_primary'],
                                   relief="flat", bd=2, padx=25, pady=15,
                                   cursor="hand2", command=self.show_online_tab,
                                   highlightthickness=0)
        self.tab_online.pack(side=tk.LEFT, padx=(0, 3))
        
        self.tab_global = tk.Button(tab_frame, text="🌍 Global Network", 
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.colors['hover'], fg=self.colors['text_secondary'],
                                   activebackground=self.colors['accent'],
                                   activeforeground=self.colors['text_primary'],
                                   relief="flat", bd=2, padx=25, pady=15,
                                   cursor="hand2", command=self.show_global_tab,
                                   highlightthickness=0)
        self.tab_global.pack(side=tk.LEFT, padx=(0, 3))
        
        self.tab_friends = tk.Button(tab_frame, text="👥 Friends", 
                                    font=("Segoe UI", 12, "bold"),
                                    bg=self.colors['hover'], fg=self.colors['text_secondary'],
                                    activebackground=self.colors['accent'],
                                    activeforeground=self.colors['text_primary'],
                                    relief="flat", bd=2, padx=25, pady=15,
                                    cursor="hand2", command=self.show_friends_tab,
                                    highlightthickness=0)
        self.tab_friends.pack(side=tk.LEFT)
        
        # Content area
        self.content_container = tk.Frame(content_frame, bg=self.colors['background'])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Build the content tabs
        self._build_online_tab()
        self._build_global_tab()
        self._build_friends_tab()

        # Start with online tab active
        self.current_tab = "online"
        self._update_tab_styling()
        
        # --- Beautiful Pastel Action Bar ---
        action_frame = tk.Frame(self, bg=self.colors['surface'], height=80)
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 25))
        action_frame.pack_propagate(False)
        
        # Action buttons with better styling
        button_frame = tk.Frame(action_frame, bg=self.colors['surface'])
        button_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=18)
        
        self.chat_btn = tk.Button(button_frame, text="💬 Start Chat", 
                                 command=self.open_selected,
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.colors['secondary'], fg=self.colors['text_primary'],
                                 activebackground=self.colors['primary_dark'],
                                 activeforeground=self.colors['text_primary'],
                                 relief="flat", bd=2, padx=30, pady=12,
                                 cursor="hand2", highlightthickness=0)
        self.chat_btn.pack(side=tk.LEFT)
        
        refresh_btn = tk.Button(button_frame, text="🔄 Refresh", 
                               command=self.refresh_current_tab,
                               font=("Segoe UI", 11, "bold"),
                               bg=self.colors['hover'], fg=self.colors['text_primary'],
                               activebackground=self.colors['accent'],
                               activeforeground=self.colors['text_primary'],
                               relief="flat", bd=2, padx=25, pady=12,
                               cursor="hand2", highlightthickness=0)
        refresh_btn.pack(side=tk.LEFT, padx=(12, 0))
        
        # Help text with better styling
        help_label = tk.Label(button_frame, text="💡 Double-click any contact to start chatting",
                             font=("Segoe UI", 10, "italic"), 
                             bg=self.colors['surface'], fg=self.colors['text_secondary'])
        help_label.pack(side=tk.RIGHT, pady=5)

        # --- networking state ---
        self.inbox: Optional[InboxServer] = None
        self.presence: Optional[Presence] = None
        self.global_discovery: Optional[GlobalDiscovery] = None
        self._tcp_port: Optional[int] = None
        self._incoming_queue: "queue.Queue[tuple]" = queue.Queue()
        self._refresh_job = None

    # ----------------------------- Modern Contact Lists -----------------------------
    def _build_online_tab(self):
        # Online users container
        self.online_frame = tk.Frame(self.content_container, bg=self.colors['background'])
        
        # Header for online users
        online_header = tk.Frame(self.online_frame, bg=self.colors['surface'], height=50)
        online_header.pack(fill=tk.X, pady=(0, 10))
        online_header.pack_propagate(False)
        
        online_title = tk.Label(online_header, text="🌐 Online Users", 
                               font=("Segoe UI", 14, "bold"),
                               bg=self.colors['surface'], fg=self.colors['text_primary'])
        online_title.pack(side=tk.LEFT, padx=20, pady=15)
        
        online_count = tk.Label(online_header, text="0 users online", 
                               font=("Segoe UI", 10),
                               bg=self.colors['surface'], fg=self.colors['text_secondary'])
        online_count.pack(side=tk.RIGHT, padx=20, pady=15)
        self.online_count_label = online_count
        
        # Scrollable frame for contacts
        canvas = tk.Canvas(self.online_frame, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.online_frame, orient="vertical", command=canvas.yview)
        self.online_scrollable = tk.Frame(canvas, bg=self.colors['background'])
        
        self.online_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.online_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.online_canvas = canvas

    def _build_global_tab(self):
        # Global users container
        self.global_frame = tk.Frame(self.content_container, bg=self.colors['background'])
        
        # Header for global users
        global_header = tk.Frame(self.global_frame, bg=self.colors['surface'], height=50)
        global_header.pack(fill=tk.X, pady=(0, 10))
        global_header.pack_propagate(False)
        
        global_title = tk.Label(global_header, text="🌍 Global Network Users", 
                               font=("Segoe UI", 14, "bold"),
                               bg=self.colors['surface'], fg=self.colors['text_primary'])
        global_title.pack(side=tk.LEFT, padx=20, pady=15)
        
        global_count = tk.Label(global_header, text="0 users online", 
                               font=("Segoe UI", 10),
                               bg=self.colors['surface'], fg=self.colors['text_secondary'])
        global_count.pack(side=tk.RIGHT, padx=20, pady=15)
        self.global_count_label = global_count
        
        # Info text
        info_text = tk.Label(global_header, text="(Requires internet connection)", 
                            font=("Segoe UI", 9),
                            bg=self.colors['surface'], fg=self.colors['text_secondary'])
        info_text.pack(side=tk.RIGHT, padx=(0, 10), pady=15)
        
        # Scrollable frame for contacts
        canvas = tk.Canvas(self.global_frame, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.global_frame, orient="vertical", command=canvas.yview)
        self.global_scrollable = tk.Frame(canvas, bg=self.colors['background'])
        
        self.global_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.global_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.global_canvas = canvas

    def _build_friends_tab(self):
        # Friends container
        self.friends_frame = tk.Frame(self.content_container, bg=self.colors['background'])
        
        # Header for friends
        friends_header = tk.Frame(self.friends_frame, bg=self.colors['surface'], height=50)
        friends_header.pack(fill=tk.X, pady=(0, 10))
        friends_header.pack_propagate(False)
        
        friends_title = tk.Label(friends_header, text="👥 Your Friends", 
                                font=("Segoe UI", 14, "bold"),
                                bg=self.colors['surface'], fg=self.colors['text_primary'])
        friends_title.pack(side=tk.LEFT, padx=20, pady=15)
        
        friends_count = tk.Label(friends_header, text="0 friends", 
                                font=("Segoe UI", 10),
                                bg=self.colors['surface'], fg=self.colors['text_secondary'])
        friends_count.pack(side=tk.RIGHT, padx=20, pady=15)
        self.friends_count_label = friends_count
        
        # Scrollable frame for contacts
        canvas = tk.Canvas(self.friends_frame, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.friends_frame, orient="vertical", command=canvas.yview)
        self.friends_scrollable = tk.Frame(canvas, bg=self.colors['background'])
        
        self.friends_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.friends_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.friends_canvas = canvas

        # Context menu: remove friend
        self._friend_menu = tk.Menu(self, tearoff=0)
        self._friend_menu.add_command(label="🗑️ Remove Friend", command=self._remove_selected_friend)

    # --------------------------- Tab Management ---------------------------
    def show_online_tab(self):
        self.current_tab = "online"
        self._update_tab_styling()
        self._show_current_tab()
    
    def show_global_tab(self):
        self.current_tab = "global"
        self._update_tab_styling()
        self._show_current_tab()
    
    def show_friends_tab(self):
        self.current_tab = "friends"
        self._update_tab_styling()
        self._show_current_tab()
    
    def _update_tab_styling(self):
        # Reset all tabs
        self.tab_online.configure(bg=self.colors['border'], fg=self.colors['text_secondary'])
        self.tab_global.configure(bg=self.colors['border'], fg=self.colors['text_secondary'])
        self.tab_friends.configure(bg=self.colors['border'], fg=self.colors['text_secondary'])
        
        # Highlight current tab
        if self.current_tab == "online":
            self.tab_online.configure(bg=self.colors['accent'], fg="white")
        elif self.current_tab == "global":
            self.tab_global.configure(bg=self.colors['accent'], fg="white")
        else:  # friends
            self.tab_friends.configure(bg=self.colors['accent'], fg="white")
    
    def _show_current_tab(self):
        # Hide all tabs
        self.online_frame.pack_forget()
        self.global_frame.pack_forget()
        self.friends_frame.pack_forget()
        
        # Show current tab
        if self.current_tab == "online":
            self.online_frame.pack(fill=tk.BOTH, expand=True)
        elif self.current_tab == "global":
            self.global_frame.pack(fill=tk.BOTH, expand=True)
        else:  # friends
            self.friends_frame.pack(fill=tk.BOTH, expand=True)

    # --------------------------- lifecycle ---------------------------
    def on_start(self):
        if self.presence is not None:
            # already online
            return

        # Start TCP server (port 0 = OS chooses a free port)
        self.inbox = InboxServer(on_incoming=self._on_incoming_socket)
        self._tcp_port = self.inbox.start("0.0.0.0", 0)

        # Start UDP presence (local network)
        name = (self.name_var.get() or "User").strip()
        self.presence = Presence(name=name, tcp_port=self._tcp_port)
        self.presence.start()
        
        # Start global discovery (cross-network)
        self.global_discovery = GlobalDiscovery(
            name=name, 
            tcp_port=self._tcp_port,
            on_peer_update=self.refresh_global
        )
        self.global_discovery.start()

        # UI
        self.status_var.set(f"● Online @ port {self._tcp_port}")
        self.go_btn.configure(text="Online", state="disabled", bg=self.colors['success'])

        # First refresh + loops
        self.refresh_online()
        self.refresh_global()
        self.refresh_friends()
        self._schedule_refresh()
        self.after(100, self._poll_incoming)

    def _schedule_refresh(self):
        self._refresh_job = self.after(1200, self._refresh_loop)

    def _refresh_loop(self):
        self.refresh_online()
        self.refresh_friends()
        self._schedule_refresh()

    # --------------------------- refreshers --------------------------
    def refresh_current_tab(self):
        if self.current_tab == "online":
            self.refresh_online()
        elif self.current_tab == "global":
            self.refresh_global()
        else:
            self.refresh_friends()

    def refresh_online(self):
        if not self.presence:
            return
        
        # Clear existing contacts
        for widget in self.online_scrollable.winfo_children():
            widget.destroy()
        
        peers = self.presence.get_active_peers()
        self.online_count_label.configure(text=f"{len(peers)} users online")
        
        now = time.time()
        for p in peers:
            last = max(0, now - p["last_seen"])
            self._create_contact_card(self.online_scrollable, p["name"], p["ip"], p["port"], 
                                    f"Last seen: {last:0.1f}s ago", "online")

    def refresh_global(self):
        """Refresh global network users."""
        if not self.global_discovery:
            return
        
        # Clear existing contacts
        for widget in self.global_scrollable.winfo_children():
            widget.destroy()
        
        peers = self.global_discovery.get_global_peers()
        self.global_count_label.configure(text=f"{len(peers)} users online globally")
        
        for p in peers:
            last_seen = time.time() - p.get('last_seen', 0)
            self._create_contact_card(self.global_scrollable, p["name"], p["public_ip"], p["tcp_port"], 
                                    f"Last seen: {last_seen:0.1f}s ago", "global")

    def refresh_friends(self):
        # Clear existing contacts
        for widget in self.friends_scrollable.winfo_children():
            widget.destroy()
        
        friends = self.storage.get_friends()
        self.friends_count_label.configure(text=f"{len(friends)} friends")
        
        for f in friends:
            last_seen = f.get("last_seen") or "Never"
            self._create_contact_card(self.friends_scrollable, f["name"], f["ip"], f["port"], 
                                    f"Last seen: {last_seen}", "friend", f)
    
    def _create_contact_card(self, parent, name, ip, port, status_text, card_type, friend_data=None):
        """Create a beautiful pastel contact card"""
        # Contact card container with subtle border
        card_frame = tk.Frame(parent, bg=self.colors['surface'], relief="flat", bd=1,
                             highlightthickness=1, highlightbackground=self.colors['border'])
        card_frame.pack(fill=tk.X, padx=12, pady=8)
        card_frame.pack_propagate(False)
        card_frame.configure(height=80)
        
        # Beautiful avatar with gradient-like effect
        avatar_frame = tk.Frame(card_frame, bg=self.colors['secondary'], width=55, height=55,
                               relief="flat", bd=0)
        avatar_frame.pack(side=tk.LEFT, padx=18, pady=12)
        avatar_frame.pack_propagate(False)
        
        # Get first letter of name for avatar with better styling
        initial = name[0].upper() if name else "?"
        avatar_label = tk.Label(avatar_frame, text=initial, 
                               font=("Segoe UI", 18, "bold"),
                               bg=self.colors['secondary'], fg=self.colors['text_primary'])
        avatar_label.pack(expand=True)
        
        # Contact info with better spacing
        info_frame = tk.Frame(card_frame, bg=self.colors['surface'])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15), pady=12)
        
        # Name with improved typography
        name_label = tk.Label(info_frame, text=name, 
                             font=("Segoe UI", 13, "bold"),
                             bg=self.colors['surface'], fg=self.colors['text_primary'])
        name_label.pack(anchor="w", pady=(0, 2))
        
        # Status with better styling
        status_label = tk.Label(info_frame, text=status_text, 
                               font=("Segoe UI", 10),
                               bg=self.colors['surface'], fg=self.colors['text_secondary'])
        status_label.pack(anchor="w", pady=(0, 2))
        
        # IP info with subtle styling
        ip_label = tk.Label(info_frame, text=f"📍 {ip}:{port}", 
                           font=("Segoe UI", 9),
                           bg=self.colors['surface'], fg=self.colors['text_secondary'])
        ip_label.pack(anchor="w")
        
        # Beautiful online indicator
        if card_type == "online":
            indicator = tk.Label(card_frame, text="🟢", font=("Segoe UI", 14),
                               bg=self.colors['surface'])
            indicator.pack(side=tk.RIGHT, padx=18, pady=30)
        elif card_type == "global":
            indicator = tk.Label(card_frame, text="🌍", font=("Segoe UI", 14),
                               bg=self.colors['surface'])
            indicator.pack(side=tk.RIGHT, padx=18, pady=30)
        
        # Bind events
        def on_click(event):
            self._select_contact(card_frame, name, ip, port)
        
        def on_double_click(event):
            self.open_selected()
        
        card_frame.bind("<Button-1>", on_click)
        card_frame.bind("<Double-1>", on_double_click)
        
        # Make all child widgets clickable too
        for widget in [avatar_frame, avatar_label, info_frame, name_label, status_label, ip_label]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Double-1>", on_double_click)
        
        # Store contact data
        card_frame.contact_data = {"name": name, "ip": ip, "port": port, "type": card_type}
        if friend_data:
            card_frame.contact_data["friend_data"] = friend_data
    
    def _select_contact(self, card_frame, name, ip, port):
        """Handle contact selection"""
        # Reset all card backgrounds
        if self.current_tab == "online":
            for widget in self.online_scrollable.winfo_children():
                if hasattr(widget, 'contact_data'):
                    widget.configure(bg=self.colors['surface'])
        elif self.current_tab == "global":
            for widget in self.global_scrollable.winfo_children():
                if hasattr(widget, 'contact_data'):
                    widget.configure(bg=self.colors['surface'])
        else:
            for widget in self.friends_scrollable.winfo_children():
                if hasattr(widget, 'contact_data'):
                    widget.configure(bg=self.colors['surface'])
        
        # Highlight selected card
        card_frame.configure(bg="#E3F2FD")
        
        # Store selected contact
        self.selected_contact = {"name": name, "ip": ip, "port": port}

    # ---------------------- incoming connections ---------------------
    def _on_incoming_socket(self, conn, addr):
        # called by server thread; push to queue for UI thread
        self._incoming_queue.put((conn, addr))

    def _poll_incoming(self):
        try:
            while True:
                conn, addr = self._incoming_queue.get_nowait()
                ip, port = addr[0], addr[1]
                # save/update friend
                self.storage.upsert_friend(ip, ip, port)
                # open a chat window that adopts this socket
                ChatWindow(
                    self, title=f"Chat ← {ip}:{port}", adopt=(conn, addr),
                    peer_name=ip, storage=self.storage
                )
        except queue.Empty:
            pass
        finally:
            self.after(150, self._poll_incoming)

    # ------------------------------ actions ------------------------------
    def open_selected(self):
        if not hasattr(self, 'selected_contact') or not self.selected_contact:
            messagebox.showinfo("Select a contact", "Please select a contact first.")
            return
        
        contact = self.selected_contact
        name = contact["name"]
        ip = contact["ip"]
        port = contact["port"]
        
        try:
            port = int(port)
        except Exception:
            messagebox.showerror("Invalid port", "Peer port is not an integer.")
            return

        # Save/update friend on connect
        self.storage.upsert_friend(name or ip, ip, port)

        # Open chat window (outgoing connection)
        ChatWindow(
            self, title=f"Chat → {name or ip} ({ip}:{port})",
            connect_to=(ip, port), peer_name=name or ip, storage=self.storage
        )

    def _popup_friend_menu(self, event):
        # Find the contact card under the cursor
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget and hasattr(widget, 'contact_data'):
            self._friend_menu.tk_popup(event.x_root, event.y_root)

    def _remove_selected_friend(self):
        if not hasattr(self, 'selected_contact') or not self.selected_contact:
            return
        
        contact = self.selected_contact
        name = contact["name"]
        ip = contact["ip"]
        port = contact["port"]
        
        try:
            port = int(port)
        except Exception:
            return
        
        # Confirm removal
        if messagebox.askyesno("Remove Friend", f"Remove {name} from your friends list?"):
            key = Storage.make_key(name, ip, port)
            self.storage.remove_friend(key)
            self.refresh_friends()
            self.selected_contact = None

    # ------------------------------ teardown ------------------------------
    def destroy(self):
        try:
            if self.presence:
                self.presence.stop()
            if self.global_discovery:
                self.global_discovery.stop()
            if self.inbox:
                self.inbox.stop()
            if self._refresh_job:
                self.after_cancel(self._refresh_job)
        finally:
            super().destroy()
