# src/app.py
import os
import sys
import subprocess
import importlib
import shutil
import time
import json
import uuid
import threading
import queue
from tkinter import ttk, filedialog, messagebox, colorchooser
import webbrowser
import tkinter as _tk  # local tkinter alias for types / fallback

# Importaciones desde otros módulos
from .constants import TARGET_FOLDERS, BEDROCK_PREFIX_REGEX
from .helpers import offline_uuid_from_name, format_uuid, find_worlds_in_dir
from .logic import process_world
from .ui_components import ScrollableTreeview

# Try to import requests and GUI helpers; if missing, try to install
def ensure_package(pkg_name, pip_name=None):
    pip_name = pip_name or pkg_name
    try:
        return importlib.import_module(pkg_name)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            return importlib.import_module(pkg_name)
        except Exception:
            return None

# GUI and network libs
tk = ensure_package("tkinter")            # tkinter is system-provided
if tk is None:
    raise RuntimeError("tkinter is required. On Linux: sudo apt install python3-tk")
requests = ensure_package("requests", "requests")
# ttkbootstrap is optional (for nicer theme); if missing, fallback to plain ttk
ttkbootstrap = ensure_package("ttkbootstrap", "ttkbootstrap")
if ttkbootstrap is not None:
    from ttkbootstrap import Style
else:
    Style = None

# Importar clases auxiliares
from .ui_builder import UIBuilder
from .logic_handlers import LogicHandlers
from .queue_manager import QueueManager

# -------------------------
# App class
# -------------------------
class UUIDConverterApp:
    def __init__(self, root):
        self.root = root
        # Language setup - Removed i18n, hardcoded English
        self.root.title("Minecraft UUID Converter v0.2.18")
        self.root.geometry("1000x740")
        # style
        if Style is not None:
            self.style = Style(theme="darkly")
        else:
            self.style = None
        # state
        self.script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.working_worlds_dir = os.path.join(self.script_dir, "working_worlds")
        self.final_worlds_dir = os.path.join(self.script_dir, "converted_worlds")
        os.makedirs(self.working_worlds_dir, exist_ok=True)
        os.makedirs(self.final_worlds_dir, exist_ok=True)
        # thread/log queue
        self.queue = queue.Queue()
        self.proc_thread = None
        self.cancel_event = threading.Event()
        self.cancel_search_event = threading.Event()
        # UI vars
        self.analyze_status_var = tk.StringVar()
        self.analysis_counter_var = tk.StringVar(value="Total: 0 / Selected: 0")
        self.load_mode_var = tk.StringVar(value="Folder") # Hardcoded
        self.search_analysis_var = tk.StringVar()
        self.search_convert_var = tk.StringVar()
        self.bedrock_to_java_offline_var = tk.BooleanVar(value=False)
        self.provider_priority_var = tk.StringVar(value="Mojang (first)")
        # self.invert_conversion_var = tk.BooleanVar(value=False) # REMOVED
        self.create_backup_var = tk.BooleanVar(value=True)
        self.show_detailed_map_var = tk.BooleanVar(value=False)
        self.conversion_mode_var = tk.StringVar(value="oto") # NEW: 'oto' or 'otof'
        # Internal state
        self.conversion_mode = "oto" # Default mode until user confirms
        # Diccionarios maestros para la búsqueda
        self.all_found_tv_items = {}
        self.all_map_tv_items = {} # Stores the 5-tuple always

        # Instanciar clases auxiliares
        self.ui_builder = UIBuilder(self)
        self.logic_handlers = LogicHandlers(self)
        self.queue_manager = QueueManager(self)

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        # Ahora llama al método en UIBuilder
        self.ui_builder.build_ui()

    # ---- Métodos de coordinación que se llaman desde otros módulos ----
    def _toggle_theme(self):
        # Ahora llama al método en UIBuilder
        self.ui_builder._toggle_theme()

    def _clear_log(self):
        # Ahora llama al método en UIBuilder
        self.ui_builder._clear_log()

    def _start_analysis(self):
        self.logic_handlers._start_analysis()

    def _find_online_uuids_for_selected(self):
        self.logic_handlers._find_online_uuids_for_selected()

    def _move_items_to_conversion(self, item_ids):
        self.logic_handlers._move_items_to_conversion(item_ids)

    def _start_processing(self):
        self.logic_handlers._start_processing()

    def _calculate_offline_uuids(self):
        self.logic_handlers._calculate_offline_uuids()

    def _poll_queue(self):
        self.queue_manager._poll_queue()

    def _append_log(self, text):
        self.queue_manager._append_log(text)

    # ---- Métodos propios de app.py (no delegados) ----
    # Métodos de UI que no están en UIBuilder pero son llamados desde ahí o por comandos de botones
    def _update_ui_for_mode(self):
        """Updates internal state and UI elements based on selected mode."""
        self.conversion_mode = self.conversion_mode_var.get()
        mode_text = 'Offline -> Online' if self.conversion_mode == 'oto' else 'Online -> Offline'
        self._append_log(f"Conversion mode set to: {mode_text}")
        # Update button states in Tab 5 (might fail if not built yet, hence try/except)
        try:
            if self.conversion_mode == 'otof':
                self.calculate_offline_btn.config(state="normal")
            else:
                self.calculate_offline_btn.config(state="disabled")
        except AttributeError:
             pass # Ignore if button doesn't exist yet

    def _confirm_mode_and_start(self):
        """Saves the selected mode and proceeds to the next tab."""
        self._update_ui_for_mode() # Ensure UI state is correct based on final selection
        self.notebook.select(1)

    # --- Métodos de Tabla de Mundos (Tab 1) ---
    def _load_world_item(self):
        path = filedialog.askdirectory(title="Select a world folder")
        if not path: return
        for iid in self.items_tv.get_children():
            if self.items_tv.item(iid)['values'][0] == path: return # Check col 0
        if not any(os.path.isdir(os.path.join(path, c)) for c in TARGET_FOLDERS):
            messagebox.showwarning("Not a World", "The folder doesn't look like a world (missing playerdata, etc.)")
            return
        self.items_tv.insert("", "end", values=(path, "N/A - Assign", "N/A", "Ready"))

    def _clear_items(self):
        for iid in self.items_tv.get_children():
            self.items_tv.delete(iid)

    def _assign_usercache(self):
        selected = self.items_tv.selection()
        if not selected:
            messagebox.showwarning("Nothing Selected", "Select a world from the list first.")
            return
        item_id = selected[0]
        uc_path = filedialog.askopenfilename(
            title="Select JSON file (usercache-like)",
            filetypes=[("JSON files", "*.json")]
        )
        if not uc_path:
            return
        try:
            current_values = self.items_tv.item(item_id)['values']
            self.items_tv.item(item_id, values=(current_values[0], uc_path, current_values[2], current_values[3]))
        except Exception as e:
            messagebox.showerror("Error", f"Could not update row: {e}")

    # --- Métodos de edición manual (Tab 4) ---
    def _edit_selected_mapping(self):
        # ... (copia aquí el código de _edit_selected_mapping de tu v0.2.18 original) ...
        # Por brevedad, no lo incluyo completo aquí, pero asegúrate de tenerlo
        pass # Reemplaza con el código real

    def _import_mappings(self):
        # ... (copia aquí el código de _import_mappings de tu v0.2.18 original) ...
        pass # Reemplaza con el código real

    def _export_mappings(self):
        # ... (copia aquí el código de _export_mappings de tu v0.2.18 original) ...
        pass # Reemplaza con el código real

    # --- Métodos de utilidad (usados en varios lados) ---
    def _open_folder(self, path):
        try:
            if sys.platform.startswith("win"): os.startfile(path)
            elif sys.platform.startswith("darwin"): subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _search_treeview(self, tree, query, master_list):
        query = query.lower().strip()
        items_to_detach = []
        items_to_attach = []
        for iid in list(master_list.keys()):
             if not tree.exists(iid): continue
             values = master_list.get(iid)
             if not values: continue
             found = False
             if not query:
                 found = True
             else:
                 for v in values:
                     if query in str(v).lower():
                         found = True
                         break
             if found:
                 if tree.parent(iid) == "":
                      items_to_attach.append(iid)
             else:
                  if tree.parent(iid) != "":
                       items_to_detach.append(iid)
        for iid in items_to_detach:
             if tree.exists(iid): tree.detach(iid)
        for iid in items_to_attach:
             if iid in master_list and tree.exists(iid):
                  tree.reattach(iid, "", "end")

    def _remove_from_map_tv(self):
        selected = self.map_tv.selection()
        for iid in selected:
            if iid in self.all_map_tv_items: del self.all_map_tv_items[iid]
            if self.map_tv.exists(iid): self.map_tv.delete(iid)

    def _toggle_map_view(self):
        is_detailed = self.show_detailed_map_var.get()
        all_master_iids = list(self.all_map_tv_items.keys())
        for iid in self.map_tv.get_children():
            self.map_tv.delete(iid)
        if is_detailed:
            self.map_tv.config(columns=("player", "source_type", "source_uuid", "target_type", "target_uuid"), show="headings")
            self.map_tv.heading("player", text="Player")
            self.map_tv.heading("source_type", text="Source Type")
            self.map_tv.heading("source_uuid", text="Source UUID")
            self.map_tv.heading("target_type", text="Target Type")
            self.map_tv.heading("target_uuid", text="Target UUID")
            self.map_tv.column("player", width=150)
            self.map_tv.column("source_type", width=140)
            self.map_tv.column("source_uuid", width=240)
            self.map_tv.column("target_type", width=140)
            self.map_tv.column("target_uuid", width=240)
            for iid in all_master_iids:
                if iid in self.all_map_tv_items:
                    values = self.all_map_tv_items[iid]
                    display_values = list(values)
                    if display_values[3] == "Pending Calculation":
                        display_values[4] = "Pending..."
                    self.map_tv.insert("", "end", iid=iid, values=tuple(display_values))
        else:
            self.map_tv.config(columns=("player", "offline", "online"), show="headings")
            self.map_tv.heading("player", text="Player")
            self.map_tv.heading("offline", text="Source UUID")
            self.map_tv.heading("online", text="Target UUID")
            self.map_tv.column("player", width=150)
            self.map_tv.column("offline", width=300)
            self.map_tv.column("online", width=300)
            for iid in all_master_iids:
                if iid in self.all_map_tv_items:
                    values = self.all_map_tv_items[iid]
                    player = values[0]
                    source_uuid = values[2]
                    target_uuid = values[4]
                    display_target = target_uuid if values[3] != "Pending Calculation" else "Pending..."
                    display_values = (player, source_uuid, display_target)
                    self.map_tv.insert("", "end", iid=iid, values=display_values)
        self._search_treeview(self.map_tv, self.search_convert_var.get(), self.all_map_tv_items)

    # --- Métodos de análisis (Tab 4) ---
    def _add_selected_to_conversion(self):
        selected_items = self.found_tv.selection()
        if not selected_items:
            messagebox.showwarning("Nothing Selected", "Select players from the comparison table.")
            return
        self._move_items_to_conversion(selected_items)

    def _add_all_to_conversion(self):
        all_items = list(self.all_found_tv_items.keys())
        if not all_items:
            messagebox.showinfo("Empty", "No players in the comparison list.")
            return
        visible_items = [iid for iid in all_items if self.found_tv.exists(iid)]
        self._move_items_to_conversion(visible_items)

    def _update_analysis_counter(self, event=None):
        total = len(self.all_found_tv_items)
        selected = len(self.found_tv.selection())
        self.analysis_counter_var.set(f"Total: {total} / Selected: {selected}")

    # --- Métodos de Tabla UUIDs (Tab 4) ---
    def build_tab_uuids(self):
        # Este método es complejo y probablemente debería estar en UIBuilder
        # Pero si lo llamas desde UIBuilder, asegúrate de que todos sus comandos (como _edit_selected_mapping)
        # estén definidos en UUIDConverterApp o sean accesibles desde UIBuilder.
        # Por ahora, lo dejamos aquí como ejemplo de lo que puede ir en app.py
        frame = self.tab_uuids
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1) # Row 3 (treeview) expands
        # 1. Controles
        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        ttk.Label(controls, text="Provider Priority:").pack(side="left", padx=(6,2))
        prov_cb = ttk.Combobox(controls, textvariable=self.provider_priority_var,
                               values=["Mojang (first)", "Ely.by (first)"], state="readonly", width=18)
        prov_cb.pack(side="left", padx=2)
        ttk.Button(controls, text="Add All ▶",
                   command=self._add_all_to_conversion).pack(side="right", padx=6)
        ttk.Button(controls, text="Add Selected ▶",
                   command=self._add_selected_to_conversion).pack(side="right", padx=6)
        # 2. Controles Bedrock, Búsqueda, Cancelar y EDICIÓN
        controls_b = ttk.Frame(frame)
        controls_b.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        bedrock_cb = ttk.Checkbutton(controls_b, text="Convert Bedrock to Java-Offline",
                                     variable=self.bedrock_to_java_offline_var)
        bedrock_cb.pack(side="left", padx=6)
        ttk.Button(controls_b, text="🌎 Search Online (Selected)",
                   command=self._find_online_uuids_for_selected).pack(side="left", padx=6)
        ttk.Button(controls_b, text="❌ Cancel Search",
                   command=lambda: self.cancel_search_event.set()).pack(side="left", padx=6)
        # ✅ NUEVO BOTÓN (ahora que _edit_selected_mapping está en app.py)
        ttk.Button(controls_b, text="✏️ Edit Selected Mapping",
                   command=self._edit_selected_mapping).pack(side="left", padx=6)
        search_entry = ttk.Entry(controls_b, textvariable=self.search_analysis_var, width=25)
        search_entry.pack(side="right", padx=6)
        ttk.Label(controls_b, text="Search:").pack(side="right")
        self.search_analysis_var.trace_add("write",
            lambda *args: self._search_treeview(
                self.found_tv,
                self.search_analysis_var.get(),
                self.all_found_tv_items
            ))
        # 3. Tabla de Jugadores Encontrados (Validated Players)
        ttk.Label(frame, text="Validated players (found in both Usercache and Playerdata).",
                  font=("Segoe UI", 9, "italic")).grid(row=2, column=0, sticky="w", padx=10, pady=(5,0))
        scrollable_found = ScrollableTreeview(frame)
        scrollable_found.grid(row=3, column=0, sticky="nsew", padx=10, pady=(2, 8))
        self.found_tv = scrollable_found.tree
        self.found_tv.config(columns=("player", "source_type", "source_uuid", "target_type", "target_uuid"), show="headings")
        self.found_tv.heading("player", text="Player")
        self.found_tv.heading("source_type", text="Source Type")
        self.found_tv.heading("source_uuid", text="Source UUID")
        self.found_tv.heading("target_type", text="Target Type")
        self.found_tv.heading("target_uuid", text="Target UUID")
        self.found_tv.column("player", width=150)
        self.found_tv.column("source_type", width=140)
        self.found_tv.column("source_uuid", width=240)
        self.found_tv.column("target_type", width=140)
        self.found_tv.column("target_uuid", width=240)
        self.found_tv.bind('<<TreeviewSelect>>', self._update_analysis_counter)
        # 4. Navegación y Contador
        nav = ttk.Frame(frame)
        nav.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Button(nav, text="◀ Back",
                   command=lambda: self.notebook.select(3)).pack(side="left")
        ttk.Label(nav, textvariable=self.analysis_counter_var).pack(side="left", padx=10)
        ttk.Button(nav, text="Next (Conversion) ▶",
                   command=lambda: self.notebook.select(5)).pack(side="right")