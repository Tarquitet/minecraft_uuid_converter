# src/ui_builder.py
import os
import time
import tkinter as tk  # <-- Importar tkinter aquí
from tkinter import ttk, filedialog, messagebox, colorchooser
import webbrowser
from .ui_components import ScrollableTreeview
from .constants import TARGET_FOLDERS

# Importar Style si está disponible
ttkbootstrap = None
try:
    import ttkbootstrap
    from ttkbootstrap import Style as TB_Style
except ImportError:
    TB_Style = None

class UIBuilder:
    def __init__(self, app_instance):
        self.app = app_instance # Referencia a la instancia de UUIDConverterApp

    def build_ui(self):
        topbar = ttk.Frame(self.app.root)
        topbar.pack(fill="x", padx=8, pady=6)
        ttk.Label(topbar, text="Minecraft UUID Converter", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(topbar, text="Toggle Theme", command=self.app._toggle_theme).pack(side="right")
        self.app.notebook = ttk.Notebook(self.app.root)
        self.app.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.app.tab_intro = ttk.Frame(self.app.notebook)
        self.app.tab_worlds = ttk.Frame(self.app.notebook)
        self.app.tab_usercache = ttk.Frame(self.app.notebook) # NEW
        self.app.tab_playerdata = ttk.Frame(self.app.notebook) # NEW
        self.app.tab_uuids = ttk.Frame(self.app.notebook)
        self.app.tab_convert = ttk.Frame(self.app.notebook)
        self.app.tab_progress = ttk.Frame(self.app.notebook)
        self.app.notebook.add(self.app.tab_intro, text="🏠 Introduction")
        self.app.notebook.add(self.app.tab_worlds, text="1 — Load and Analyze")
        self.app.notebook.add(self.app.tab_usercache, text="2 — Usercache Data") # NEW
        self.app.notebook.add(self.app.tab_playerdata, text="3 — Playerdata Data") # NEW
        self.app.notebook.add(self.app.tab_uuids, text="4 — Comparison & Mapping")
        self.app.notebook.add(self.app.tab_convert, text="5 — Convert")
        self.app.notebook.add(self.app.tab_progress, text="📊 Progress and Log") # Renamed
        self._build_tab_intro()
        self._build_tab_worlds()
        self._build_tab_usercache() # NEW
        self._build_tab_playerdata() # NEW
        self.app.build_tab_uuids() # Llama al método en app.py que ahora contiene la lógica de la pestaña 4
        self._build_tab_convert()
        self._build_tab_progress()

    # ---- Tab 6: Progress & Log ----
    def _build_tab_progress(self):
        frame = self.app.tab_progress
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1) # Log text (row 1) expands
        log_frame = ttk.LabelFrame(frame, text="Progress and Log")
        log_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1) # El Text widget
        self.app.overall_progress = ttk.Progressbar(log_frame, orient="horizontal", length=500, mode="determinate")
        self.app.overall_progress.grid(row=0, column=0, sticky="ew", padx=6, pady=4) # Moved to row 0
        self.app.log_text = tk.Text(log_frame, height=25, state="disabled")
        self.app.log_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=4) # Moved to row 1
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.app.log_text.yview)
        log_scroll.grid(row=1, column=1, sticky="ns") # Moved to row 1
        self.app.log_text.config(yscrollcommand=log_scroll.set)
        clear_log_btn = ttk.Button(frame, text="Clear Log", command=self.app._clear_log)
        clear_log_btn.grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10)) # Moved to row 1

    # ---- Tab 0: Intro ----
    def _build_tab_intro(self):
        frame = self.app.tab_intro
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1) # Text widget now at row 2
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        ttk.Label(title_frame, text="Welcome to the Minecraft UUID Converter", font=("Segoe UI", 16, "bold")).pack()
        author_frame = ttk.Frame(title_frame)
        author_frame.pack()
        ttk.Label(author_frame, text="Author: Tarquitet", font=("Segoe UI", 10, "italic")).pack(side="left", padx=5)
        link = ttk.Label(author_frame, text="Visit my GitHub", foreground="blue", cursor="hand2", font=("Segoe UI", 10, "underline italic"))
        link.pack(side="left", padx=5)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/Tarquitet"))
        # --- NEW: Conversion Mode Selection ---
        self.app.mode_frame = ttk.LabelFrame(frame, text="Select Conversion Mode", padding=10)
        self.app.mode_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        rb_oto = ttk.Radiobutton(self.app.mode_frame,
                                 text="Offline UUID -> Online UUID (Default)",
                                 variable=self.app.conversion_mode_var,
                                 value="oto",
                                 command=self.app._update_ui_for_mode) # Add command
        rb_oto.pack(anchor="w", pady=2)
        rb_otof = ttk.Radiobutton(self.app.mode_frame,
                                  text="Online UUID -> Offline UUID (Invert)",
                                  variable=self.app.conversion_mode_var,
                                  value="otof",
                                  command=self.app._update_ui_for_mode) # Add command
        rb_otof.pack(anchor="w", pady=2)
        # --- End NEW ---
        # Tutorial Text
        text_frame = ttk.LabelFrame(frame, text="Quick Tutorial", padding=15)
        text_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10) # Moved to row 2
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        tutorial_text = """
        Welcome! This tool simplifies player data migration on Minecraft servers.
        **IMPORTANT:** First, select the **Conversion Mode** above.
        **Modes Explained:**
        * **Offline UUID -> Online UUID (Default):** Select this if you are moving players from an offline-mode server (or players who joined in offline mode) to an online-mode configuration. The tool will find the correct Online UUID for each player and copy their data.
        * **Online UUID -> Offline UUID (Invert):** Select this if you are moving players from an online-mode server *back* to an offline-mode setup. The tool will calculate the standard Offline UUID for each player and copy their data from the Online UUID to the Offline UUID.
        **NEW IN v0.2.18:**
        * You can now **edit the target UUID** of any validated player manually (Tab 4).
        * This enables **cross-player mapping** (Player A → Player B).
        * The tool prevents **duplicate target UUIDs** to avoid overwrites.
        **Detailed Steps:**
        **1. "Load and Analyze" Tab:**
        -   **Load:** Use `📂 Load World Folder...` for your *original* world.
        -   **Assign JSON:** Use `📇 Assign JSON file` to link its `usercache.json`.
        -   **Analyze:** Click `🔎 Analyze Selected World`. This creates a *copy* in `working_worlds` and analyzes it.
        **2. "Usercache Data" / 3. "Playerdata Data" Tabs:**
        -   Show raw data found in the working copy.
        **4. "Comparison & Mapping" Tab:**
        -   Shows validated players.
        -   **Search Online:** Use `🌎 Search Online` to confirm Online status (Mojang/Ely.by) using names. This updates "Source Type" if needed.
        -   **Add to Conversion:** Move players to the final plan (Tab 5).
            - In **Offline->Online** mode, only players with a found Online UUID target are added.
            - In **Online->Offline** mode, only players confirmed as "Online (Mojang/Ely.by)" are added, initially with a "Pending" target.
        -   **✏️ Edit Selected Mapping:** Click to assign a custom target UUID (any player!).
        **5. "Convert" Tab:**
        -   **Final Check:** Review the plan. Use "Show Detailed View" if needed.
        -   **(NEW)** If in **Online->Offline** mode, click **`Calculate Offline UUIDs`** first. This fills the Target UUIDs.
        -   **Start:** Select the analyzed world in **Tab 1**, then click `🚀 START CONVERSION`.
        -   This creates *another copy* in `converted_worlds` and performs file copying based on the **mode** and the **final map**.
        Done! Check the `converted_worlds` folder.
        """
        self.app.tutorial_text_widget = tk.Text(text_frame, wrap="word", height=10, font=("Segoe UI", 10)) # Reduced height slightly
        self.app.tutorial_text_widget.insert("1.0", tutorial_text)
        # Configurar color de fondo inicial
        bg_color = self.app.style.colors.get('bg') if self.app.style else self.app.root.cget('bg')
        self.app.tutorial_text_widget.config(state="disabled", relief="flat", bg=bg_color)
        self.app.tutorial_text_widget.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.app.tutorial_text_widget.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.app.tutorial_text_widget.config(yscrollcommand=scroll.set)
        # Navigation
        nav_frame = ttk.Frame(frame)
        nav_frame.grid(row=3, column=0, sticky="e", padx=20, pady=10) # Moved to row 3
        # Modified command to save mode
        ttk.Button(nav_frame, text="Start →", command=self.app._confirm_mode_and_start).pack()

    # ---- Tab 1: Worlds ----
    def _build_tab_worlds(self):
        frame = self.app.tab_worlds
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1) # Table (row 1) expands
        # 1. Controles de Carga y Asignación (Combined)
        load_frame = ttk.Frame(frame)
        load_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(load_frame, text="📂 Load World Folder...", command=self.app._load_world_item).pack(side="left", padx=6)
        ttk.Button(load_frame, text="📇 Assign JSON file (usercache-like)",
                   command=self.app._assign_usercache).pack(side="left", padx=6)
        ttk.Button(load_frame, text="🗑 Clear List", command=self.app._clear_items).pack(side="left", padx=6)
        # 2. Tabla de Mundos
        scrollable_items = ScrollableTreeview(frame, height=10)
        self.app.items_tv = scrollable_items.tree
        self.app.items_tv.config(columns=("original_path", "usercache_path", "working_path", "status"), show="headings")
        self.app.items_tv.heading("original_path", text="Original World Path")
        self.app.items_tv.heading("usercache_path", text="JSON File Path")
        self.app.items_tv.heading("working_path", text="Working Copy Path")
        self.app.items_tv.heading("status", text="Status")
        self.app.items_tv.column("original_path", width=300)
        self.app.items_tv.column("usercache_path", width=300)
        self.app.items_tv.column("working_path", width=250)
        self.app.items_tv.column("status", width=100, stretch=False)
        scrollable_items.grid(row=1, column=0, sticky="nsew", padx=10, pady=8) # Row 1
        # 3. Botón de Analizar
        analyze_frame = ttk.Frame(frame)
        analyze_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10) # Row 2
        ttk.Label(analyze_frame, textvariable=self.app.analyze_status_var).pack(side="left", padx=6)
        ttk.Button(analyze_frame, text="🔎 Analyze Selected World",
                   command=self.app._start_analysis).pack(side="right", padx=6)
        ttk.Button(analyze_frame, text="Next ▶",
                   command=lambda: self.app.notebook.select(2)).pack(side="right")

    # ---- Tab 2: Usercache (NEW) ----
    def _build_tab_usercache(self):
        frame = self.app.tab_usercache
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text="Raw data found in the assigned JSON file.",
                  font=("Segoe UI", 9, "italic")).grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        scrollable_tree = ScrollableTreeview(frame)
        self.app.usercache_tv = scrollable_tree.tree
        self.app.usercache_tv.config(columns=("player", "uuid"), show="headings")
        self.app.usercache_tv.heading("player", text="Player Name")
        self.app.usercache_tv.heading("uuid", text="UUID (from JSON)")
        self.app.usercache_tv.column("player", width=200)
        self.app.usercache_tv.column("uuid", width=300)
        scrollable_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        nav = ttk.Frame(frame)
        nav.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(nav, text="◀ Back",
                   command=lambda: self.app.notebook.select(1)).pack(side="left")
        ttk.Button(nav, text="Next (Playerdata) ▶",
                   command=lambda: self.app.notebook.select(3)).pack(side="right")

    # ---- Tab 3: Playerdata (NEW) ----
    def _build_tab_playerdata(self):
        frame = self.app.tab_playerdata
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text="Raw UUIDs found in the world's 'playerdata' folder.",
                  font=("Segoe UI", 9, "italic")).grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        scrollable_tree = ScrollableTreeview(frame)
        self.app.playerdata_tv = scrollable_tree.tree
        self.app.playerdata_tv.config(columns=("uuid",), show="headings")
        self.app.playerdata_tv.heading("uuid", text="UUID (from .dat file)")
        self.app.playerdata_tv.column("uuid", width=300)
        scrollable_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        nav = ttk.Frame(frame)
        nav.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(nav, text="◀ Back",
                   command=lambda: self.app.notebook.select(2)).pack(side="left")
        ttk.Button(nav, text="Next (Comparison) ▶",
                   command=lambda: self.app.notebook.select(4)).pack(side="right")

    # ---- Tab 5: Convert ----
    def _build_tab_convert(self):
        frame = self.app.tab_convert
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        top_controls = ttk.Frame(frame)
        top_controls.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        backup_cb = ttk.Checkbutton(top_controls, text="Create Backup (.bak)",
                                    variable=self.app.create_backup_var)
        backup_cb.pack(side="left", padx=(0, 10))
        detailed_cb = ttk.Checkbutton(top_controls, text="Show Detailed View",
                                      variable=self.app.show_detailed_map_var,
                                      command=self.app._toggle_map_view)
        detailed_cb.pack(side="left", padx=10)
        self.app.calculate_offline_btn = ttk.Button(top_controls,
                                                text="Calculate Offline UUIDs",
                                                command=self.app._calculate_offline_uuids,
                                                state="disabled")
        self.app.calculate_offline_btn.pack(side="left", padx=10)
        self.app._update_ui_for_mode()
        search_entry = ttk.Entry(top_controls, textvariable=self.app.search_convert_var, width=25)
        search_entry.pack(side="right", padx=6)
        ttk.Label(top_controls, text="Search:").pack(side="right")
        self.app.search_convert_var.trace_add("write",
            lambda *args: self.app._search_treeview(
                self.app.map_tv,
                self.app.search_convert_var.get(),
                self.app.all_map_tv_items
            ))
        map_frame = ttk.LabelFrame(frame, text="Final Conversion Map")
        map_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        scrollable_map = ScrollableTreeview(map_frame, height=8)
        self.app.map_tv = scrollable_map.tree
        self.app._toggle_map_view()
        scrollable_map.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        map_controls = ttk.Frame(map_frame)
        map_controls.grid(row=1, column=0, sticky="ew", padx=6, pady=4)
        ttk.Button(map_controls, text="🗑 Remove Selected",
                   command=self.app._remove_from_map_tv).pack(side="left")
        ttk.Button(map_controls, text="Import JSON", command=self.app._import_mappings).pack(side="left", padx=6)
        ttk.Button(map_controls, text="Export JSON", command=self.app._export_mappings).pack(side="left", padx=6)
        bottom_controls = ttk.Frame(frame)
        bottom_controls.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(bottom_controls, text="Open Converted Worlds Folder", command=lambda: self.app._open_folder(self.app.final_worlds_dir)).pack(side="right")
        ttk.Button(bottom_controls, text="🚀 START CONVERSION", command=self.app._start_processing).pack(side="right", padx=6)
        ttk.Button(bottom_controls, text="◀ Back", command=lambda: self.app.notebook.select(4)).pack(side="left")

    def _toggle_theme(self):
        # Accede a self.app.style y self.app.tutorial_text_widget
        if TB_Style is None:
            messagebox.showinfo("Theme", "ttkbootstrap not installed — theme toggle unavailable.")
            return
        current = self.app.style.theme.name # Usar self.app.style
        new = "flatly" if current == "darkly" else "darkly"
        self.app.style.theme_use(new) # Usar self.app.style
        # Actualizar color de fondo del texto de tutorial
        bg_color = self.app.style.colors.get('bg') if self.app.style else self.app.root.cget('bg') # Usar self.app.style
        if bg_color:
             self.app.tutorial_text_widget.config(bg=bg_color) # Usar self.app.tutorial_text_widget
             # Update radio button background if needed (less critical)
             # try: self.app.mode_frame.configure(background=bg_color) except: pass

    def _clear_log(self):
        """Limpia el contenido del widget de log."""
        try:
            self.app.log_text.config(state="normal") # Usar self.app.log_text
            self.app.log_text.delete(1.0, tk.END) # Usar self.app.log_text
            self.app.log_text.config(state="disabled") # Usar self.app.log_text
        except Exception:
            pass # Ignorar si hay error