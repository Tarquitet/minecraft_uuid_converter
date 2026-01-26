# src/logic_handlers.py
import os
import shutil
import time
import json
import uuid
import threading
from .constants import TARGET_FOLDERS, BEDROCK_PREFIX_REGEX
from .helpers import offline_uuid_from_name, format_uuid
from .logic import process_world

# Importar requests de la misma manera que en app.py
requests = None # Define la variable por si acaso
try:
    import requests
except ImportError:
    pass # requests no está disponible, manejarlo en la lógica

class LogicHandlers:
    def __init__(self, app_instance):
        self.app = app_instance

    def _start_analysis(self):
        selected = self.app.items_tv.selection()
        if not selected:
            messagebox.showwarning("Nothing Selected", "Select a world from the list to analyze.")
            return
        item_id = selected[0]
        values = self.app.items_tv.item(item_id)['values']
        original_path, usercache_path, _, _ = values
        self.app.analyze_status_var.set("Analyzing...")
        self.app._append_log(f"Starting analysis of: {original_path}")
        for i in self.app.found_tv.get_children(): self.app.found_tv.delete(i)
        for i in self.app.usercache_tv.get_children(): self.app.usercache_tv.delete(i)
        for i in self.app.playerdata_tv.get_children(): self.app.playerdata_tv.delete(i)
        self.app.all_found_tv_items.clear()
        for i in self.app.map_tv.get_children(): self.app.map_tv.delete(i)
        self.app.all_map_tv_items.clear()
        self.app._update_analysis_counter()
        is_valid_json_path = os.path.isfile(usercache_path)
        if not is_valid_json_path:
            if not messagebox.askyesno("JSON File Not Found",
                "No valid JSON file was found or assigned.\n"
                "Do you want to continue analyzing only the 'playerdata' folder? (Player names will not be available)."):
                self.app.analyze_status_var.set("")
                return
            usercache_path = None
        threading.Thread(target=self._worker_analysis,
                         args=(item_id, original_path, usercache_path),
                         daemon=True).start()

    def _copy_world_to_working_dir_synclog(self, original_path, working_path, log_fn):
        log_fn(f"Copying data from {original_path} to {working_path}...")
        os.makedirs(working_path, exist_ok=True)
        copied_count = 0
        for folder in TARGET_FOLDERS:
            src_folder = os.path.join(original_path, folder)
            dst_folder = os.path.join(working_path, folder)
            if os.path.isdir(src_folder):
                try:
                    if os.path.exists(dst_folder):
                         shutil.rmtree(dst_folder)
                    shutil.copytree(src_folder, dst_folder) # ✅ CORREGIDO: copyteam -> copytree
                    log_fn(f"  Copied folder: {folder}")
                    copied_count += 1
                except Exception as e:
                    log_fn(f"  ERROR copying {folder}: {e}")
            else:
                log_fn(f"  Skipping missing folder: {folder}")
        if copied_count == 0:
            try:
                os.rmdir(working_path) # Remove empty dir
            except Exception:
                pass
            raise Exception("No valid data folders (playerdata, stats, etc.) were found to copy.")
        log_fn(f"Working copy created successfully.")
        return True

    def _worker_analysis(self, item_id, original_path, usercache_path):
        world_name = os.path.basename(os.path.normpath(original_path))
        timestamp = int(time.time())
        working_path = os.path.join(self.app.working_worlds_dir, f"{world_name}_{timestamp}")
        log = lambda msg: self.app.queue.put(("log", msg))
        world_to_scan = ""
        valid_players_from_cache = []
        players_found = 0
        try:
            if os.path.exists(working_path):
                 log(f"Removing existing working directory: {working_path}")
                 shutil.rmtree(working_path)
            log(f"Creating working copy for {world_name}...")
            self._copy_world_to_working_dir_synclog(original_path, working_path, log)
            world_to_scan = working_path
            playerdata_uuids_no_hyphens = set()
            playerdata_dir = os.path.join(world_to_scan, "playerdata")
            if os.path.isdir(playerdata_dir):
                try:
                    log(f"Reading folder: {playerdata_dir}")
                    for f in os.listdir(playerdata_dir):
                        if f.endswith(".dat"):
                            uuid_from_file = os.path.splitext(f)[0]
                            uuid_no_hyphens = uuid_from_file.replace('-', '')
                            if len(uuid_no_hyphens) == 32:
                                playerdata_uuids_no_hyphens.add(uuid_no_hyphens)
                                uuid_with_hyphens = format_uuid(uuid_no_hyphens)
                                self.app.queue.put(("add_playerdata_row", (uuid_with_hyphens,)))
                            else:
                                log(f"  -> Ignoring invalid file: {f}")
                    log(f"Total {len(playerdata_uuids_no_hyphens)} valid UUIDs found in playerdata.")
                except Exception as e:
                    log(f"⚠️ Error reading playerdata folder: {e}")
            else:
                 log(f"⚠️ Folder not found or inaccessible: {playerdata_dir}")
            if not usercache_path:
                log("No JSON file provided. Listing from 'playerdata'...")
                if not playerdata_uuids_no_hyphens:
                     raise Exception("No file provided and 'playerdata' folder is empty or unreadable.")
                for uuid_nh in playerdata_uuids_no_hyphens:
                    uuid_with_hyphens = format_uuid(uuid_nh)
                    payload = ("", "Offline?", uuid_with_hyphens, "", "")
                    self.app.queue.put(("add_analysis_row", payload))
                    players_found += 1
                log(f"'playerdata' analysis complete. Listed {players_found} UUIDs for comparison.")
            else:
                filename = os.path.basename(usercache_path)
                log(f"Validating file '{filename}' against world data...")
                try:
                    with open(usercache_path, "r", encoding="utf-8") as f:
                        usercache_data = json.load(f)
                    if not isinstance(usercache_data, list):
                        raise ValueError("Invalid format: Expected a JSON list.")
                except Exception as e:
                    raise Exception(f"Error reading or parsing JSON file: {e}")
                log(f"Reading players from '{filename}':")
                
                # 🛠️ CORRECCIÓN #2: Ordenar y limitar para no colapsar Tkinter
                # Ordenamos por fecha de expiración (los más recientes primero)
                usercache_data.sort(key=lambda x: x.get("expiresOn", ""), reverse=True)
                
                display_limit = 2000
                shown_count = 0

                for entry in usercache_data:
                    if not isinstance(entry, dict): continue
                    name = entry.get("name")
                    uuid_str_hyphens = entry.get("uuid")
                    if not name or not uuid_str_hyphens: continue
                    
                    # Solo enviamos a la Interfaz Gráfica los primeros 2,000
                    if shown_count < display_limit:
                        self.app.queue.put(("add_usercache_row", (name, uuid_str_hyphens)))
                        shown_count += 1

                    # La LÓGICA INTERNA sí procesa absolutamente todos
                    uuid_str_no_hyphens = uuid_str_hyphens.replace('-', '')
                    if uuid_str_no_hyphens in playerdata_uuids_no_hyphens:
                        account_type = "Offline (Java)"
                        match = BEDROCK_PREFIX_REGEX.match(name)
                        if match: account_type = "Offline (Bedrock)"
                        payload = (name, account_type, uuid_str_hyphens, "", "")
                        valid_players_from_cache.append(payload)

                if len(usercache_data) > display_limit:
                    log(f"⚠️ UI Limit: Visualizando 2,000 de {len(usercache_data)} jugadores (El análisis interno usa todos).")
                if not valid_players_from_cache:
                    error_msg = "No UUID from the file '{filename}' matches the saved data in the 'playerdata' folder of this world.\nPlease ensure you select the correct file for:\n{world_path}".format(
                        filename=filename, world_path=world_to_scan
                    )
                    self.app.queue.put(("analysis_error_validation", (error_msg, item_id)))
                    return
                for payload in valid_players_from_cache:
                    self.app.queue.put(("add_analysis_row", payload))
                    players_found += 1
                log(f"Validation complete. Found {players_found} matching players.")
            self.app.queue.put(("analysis_done", (players_found, item_id, working_path)))
        except Exception as e:
            log(f"❌ Error during analysis: {e}")
            self.app.queue.put(("analysis_error", (str(e), item_id)))
        finally:
            self.app.queue.put(("analysis_status_clear", None))

    def _find_online_uuids_for_selected(self):
        if requests is None:
            messagebox.showerror("Error", "'requests' library is required.")
            return
        selected_items = self.app.found_tv.selection()
        if not selected_items:
            messagebox.showwarning("Nothing Selected", "Select players from the table first.")
            return
        self.app._append_log(f"Starting online search for {len(selected_items)} players...")
        self.app.cancel_search_event.clear()
        bedrock_offline_mode = self.app.bedrock_to_java_offline_var.get()
        provider_pref = self.app.provider_priority_var.get()
        threading.Thread(target=self._worker_find_uuids,
                         args=(selected_items, bedrock_offline_mode, provider_pref),
                         daemon=True).start()

    def _worker_find_uuids(self, item_ids, bedrock_offline_mode, provider_pref):
        search_order = [
            ("Mojang", "https://api.mojang.com/users/profiles/minecraft/"),
            ("Ely.by", "https://authserver.ely.by/api/users/profiles/minecraft/")
        ]
        if provider_pref == "Ely.by (first)":
            search_order.reverse()
        for item_id in item_ids:
            if self.app.cancel_search_event.is_set():
                self.app.queue.put(("log", "Search cancelled by user."))
                break
            try:
                tk_var_name = item_id + "_values"
                if not self.app.root.getvar(tk_var_name):
                     self.app._append_log(f"Warning: TK variable {tk_var_name} not found in worker (item might be gone).")
                     continue
                payload = self.app.root.globalgetvar(tk_var_name)
                if not isinstance(payload, (list, tuple)) or len(payload) != 5:
                    self.app._append_log(f"Warning: Invalid payload found for {item_id} in worker: {payload}")
                    continue
                player_name, source_type, source_uuid, _, _ = payload
                java_name = player_name
                is_bedrock = "Bedrock" in source_type
                if is_bedrock:
                    match = BEDROCK_PREFIX_REGEX.match(player_name)
                    if match: java_name = match.group(1)
                if not java_name:
                    self.app.queue.put(("log", f"Skipping {player_name}: no name to search."))
                    continue
                if is_bedrock and bedrock_offline_mode:
                    calculated_uuid = offline_uuid_from_name(java_name)
                    target_type = "Bedrock -> Java Offline"
                    self.app.queue.put(("update_analysis_table", (item_id, calculated_uuid, target_type)))
                    continue
                online_uuid = None
                found_provider = None
                for provider_name, url_base in search_order:
                    if self.app.cancel_search_event.is_set(): break
                    try:
                        r = requests.get(f"{url_base}{java_name}", timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            raw = data.get("id", "")
                            online_uuid = format_uuid(raw)
                            found_provider = provider_name
                            break
                    except Exception:
                        pass
                target_type = found_provider if found_provider else "Not Found"
                display_uuid = online_uuid or "NOT FOUND"
                if online_uuid and online_uuid == source_uuid:
                    target_type = ("Already Online", found_provider)
                    display_uuid = "N/A (Already Online)"
                self.app.queue.put(("update_analysis_table", (item_id, display_uuid, target_type)))
            except Exception as e:
                 import traceback
                 self.app.queue.put(("log", f"Error searching item {item_id}: {e}\n{traceback.format_exc()}"))
                 pass

    def _move_items_to_conversion(self, item_ids):
        added_count = 0
        skipped_count = 0
        mode = self.app.conversion_mode
        existing_sources = {v[2] for v in self.app.all_map_tv_items.values()}
        for item_id in item_ids:
            if not self.app.found_tv.exists(item_id): continue
            tk_var_name = item_id + "_values"
            if not self.app.root.getvar(tk_var_name):
                 self.app._append_log(f"Warning: TK variable {tk_var_name} not found for move.")
                 skipped_count += 1
                 continue
            values = self.app.root.globalgetvar(tk_var_name)
            if not isinstance(values, (list, tuple)) or len(values) != 5:
                self.app._append_log(f"Warning: Invalid payload found for {item_id} during move: {values}")
                skipped_count += 1
                continue
            player, source_type, source_uuid, target_type, target_uuid = values
            master_values = None
            # ✅ NUEVO: manejar mapeos manuales
            if target_type == "Manual Edit":
                if source_uuid and target_uuid and target_uuid != "NOT FOUND":
                    master_values = values
                    existing_sources.add(source_uuid)
                else:
                    skipped_count += 1
            elif mode == "oto":
                if target_uuid == "N/A (Already Online)" or target_uuid == "NOT FOUND":
                    skipped_count += 1
                    continue
                if source_uuid in existing_sources:
                    skipped_count += 1
                    self.app.queue.put(("log", f"Skipping {player} (oto): Source UUID {source_uuid[:8]}... already in final map."))
                    continue
                master_values = values
                existing_sources.add(source_uuid)
            elif mode == "otof":
                 if not source_type.startswith("Online"):
                     skipped_count += 1
                     continue
                 if source_uuid in existing_sources:
                     skipped_count += 1
                     self.app.queue.put(("log", f"Skipping {player} (otof): Source UUID {source_uuid[:8]}... already in final map."))
                     continue
                 master_values = (
                     player,
                     source_type,
                     source_uuid,
                     "Pending Calculation",
                     ""
                 )
                 existing_sources.add(source_uuid)
                 self.app.queue.put(("log", f"Added {player} ({source_type}) for offline calculation."))
            if master_values:
                new_iid = item_id
                self.app.all_map_tv_items[new_iid] = master_values
                if self.app.show_detailed_map_var.get():
                    display_values = list(master_values)
                    if display_values[3] == "Pending Calculation":
                        display_values[4] = "Pending..."
                    self.app.map_tv.insert("", "end", iid=new_iid, values=tuple(display_values))
                else:
                    display_target = master_values[4] if master_values[3] != "Pending Calculation" else "Pending..."
                    display_values = (master_values[0], master_values[2], display_target)
                    self.app.map_tv.insert("", "end", iid=new_iid, values=display_values)
                if item_id in self.app.all_found_tv_items: del self.app.all_found_tv_items[item_id]
                try:
                    if self.app.found_tv.exists(item_id): self.app.found_tv.delete(item_id)
                except Exception as e:
                     self.app._append_log(f"Warning: Could not delete item {item_id} from found_tv: {e}")
                added_count += 1
        log_msg = f"Added {added_count} player(s) to the final conversion list for mode '{mode}'."
        if skipped_count > 0:
             log_msg += f" Skipped {skipped_count} (duplicates or not applicable to mode - see log)."
             messagebox.showwarning("Players Skipped",
                f"{skipped_count} players were skipped (duplicates or not applicable to mode). See log for details.")
        self.app._append_log(log_msg)
        if added_count > 0: self.app.notebook.select(5)
        self.app._update_analysis_counter()

    def _start_processing(self):
        selected = self.app.items_tv.selection()
        if not selected:
            messagebox.showwarning("No World Selected", "Select an *analyzed* world from the 'Load and Analyze' tab (Tab 1) first.")
            return
        item_id = selected[0]
        values = self.app.items_tv.item(item_id)['values']
        original_path, _, working_path, status = values
        if status != "Analyzed" or not os.path.isdir(working_path):
             messagebox.showwarning("World Not Analyzed", "The selected world has not been analyzed successfully. Please analyze it first (Tab 1).")
             return
        mappings_for_conversion = []
        mode = self.app.conversion_mode
        processed_count = 0
        skipped_count = 0
        pending_calculation = False
        for iid, values in self.app.all_map_tv_items.items():
            player, source_type, source_uuid, target_type, target_uuid = values
            uuid_from = None
            uuid_to = None
            should_process = False
            # ✅ NUEVO: procesar mapeos manuales
            if target_type == "Manual Edit":
                if source_uuid and target_uuid:
                    mappings_for_conversion.append((player, source_uuid, target_uuid))
                    processed_count += 1
                else:
                    skipped_count += 1
                continue
            if mode == "oto":
                if target_type != "Offline (Calculated)" and target_type != "Pending Calculation":
                     uuid_from = source_uuid
                     uuid_to = target_uuid
                     should_process = True
                else:
                    skipped_count += 1
            elif mode == "otof":
                 if target_type == "Offline (Calculated)":
                      uuid_from = source_uuid
                      uuid_to = target_uuid
                      should_process = True
                 elif target_type == "Pending Calculation":
                      pending_calculation = True
                      skipped_count += 1
                 else:
                     skipped_count += 1
            if should_process and uuid_from and uuid_to:
                 mappings_for_conversion.append((player, uuid_from, uuid_to))
                 processed_count += 1
            elif should_process:
                self.app._append_log(f"Warning: Invalid UUIDs for {player} in mode {mode}. Skipping.")
                skipped_count +=1
        if pending_calculation and mode == 'otof':
             messagebox.showerror("Calculation Needed", "You are in Online -> Offline mode, but some players still need their Offline UUID calculated.\nPlease click the 'Calculate Offline UUIDs' button first.")
             return
        if not mappings_for_conversion:
            messagebox.showwarning("No Mappings for Mode", f"No valid mappings were found ready for conversion in the selected mode ('{'Offline -> Online' if mode == 'oto' else 'Online -> Offline'}').")
            return
        if skipped_count > 0:
             self.app._append_log(f"Skipped {skipped_count} mappings not applicable or ready for the current conversion mode.")
        create_backup = self.app.create_backup_var.get()
        total_ops = 0
        uuid_from_col = {m[1] for m in mappings_for_conversion}
        for folder in TARGET_FOLDERS:
            fp = os.path.join(working_path, folder)
            if os.path.isdir(fp):
                try:
                    for f in os.listdir(fp):
                        if os.path.splitext(f)[0] in uuid_from_col:
                            total_ops += 1
                except Exception as e:
                    self.app.queue.put(("log", f"Error estimating ops in {fp}: {e}"))
        if total_ops == 0:
            if not messagebox.askyesno("No matches", "No files matching the required source UUIDs were detected in the working copy for the selected mode. This might happen if the source files don't exist. Continue anyway?"):
                return
        self.app.overall_progress["maximum"] = max(1, total_ops)
        self.app.overall_progress["value"] = 0
        self.app.cancel_event.clear()
        self.app.proc_thread = threading.Thread(target=self._processing_worker,
                                            args=(working_path, mappings_for_conversion, create_backup, total_ops),
                                            daemon=True)
        self.app.proc_thread.start()

    def _processing_worker(self, working_path, mappings, create_backup, total_ops):
        overall_done = 0
        log = lambda s: self.app.queue.put(("log", s))
        def inc_overall(n=1):
            nonlocal overall_done
            overall_done += n
            self.app.queue.put(("overall", min(overall_done, self.app.overall_progress['maximum'])))
        def per_file_cb():
            inc_overall(1)
        try:
            log(f"Starting conversion for: {working_path} (Mode: {'Offline -> Online' if self.app.conversion_mode == 'oto' else 'Online -> Offline'})")
            world_name = os.path.basename(os.path.normpath(working_path))
            timestamp = int(time.time())
            final_path = os.path.join(self.app.final_worlds_dir, f"{world_name}_converted_{timestamp}")
            if os.path.exists(final_path):
                log(f"Warning: Output folder {final_path} already exists. Removing old one.")
                try:
                    shutil.rmtree(final_path)
                except Exception as e:
                    log(f"❌ Failed to remove existing output folder: {e}")
                    raise Exception(f"Failed to remove existing output folder: {e}")
            log(f"Creating final copy at: {final_path}")
            shutil.copytree(working_path, final_path)
            actual_ops = process_world(final_path, mappings, create_backup, log, progress_callback=per_file_cb)
            progress_ratio = actual_ops / total_ops if total_ops > 0 else 1.0
            if progress_ratio < 1.0:
                 self.app.queue.put(("overall", total_ops))
            elif actual_ops > self.app.overall_progress['maximum']:
                 self.app.queue.put(("overall_max_adjust", actual_ops))
            log(f"Processing finished. Performed {actual_ops} copy operations.")
            log(f"✅ Success! Converted world saved to: {final_path}")
            self.app.queue.put(("done", None))
        except Exception as e:
            log(f"❌ FATAL ERROR during conversion: {e}")
            import traceback
            log(traceback.format_exc())
            self.app.queue.put(("log", "Processing aborted due to error."))

    def _calculate_offline_uuids(self):
        if self.app.conversion_mode != 'otof':
            messagebox.showwarning("Wrong Mode", "Offline UUID calculation is only available in 'Online -> Offline' mode.")
            return
        calculated_count = 0
        updated_items = {}
        self.app._append_log("Calculating offline UUIDs...")
        for iid, values in self.app.all_map_tv_items.items():
            player, source_type, source_uuid, target_type, target_uuid = values
            if target_type == "Pending Calculation" or (target_type == "" and "Online" in source_type):
                try:
                    offline_uuid = offline_uuid_from_name(player)
                    updated_items[iid] = (
                        player,
                        source_type,
                        source_uuid,
                        "Offline (Calculated)",
                        offline_uuid
                    )
                    calculated_count += 1
                except Exception as e:
                     self.app._append_log(f"Error calculating offline UUID for {player}: {e}")
        self.app.all_map_tv_items.update(updated_items)
        self.app._toggle_map_view()
        self.app._append_log(f"Calculated offline UUIDs for {calculated_count} player(s).")
        if calculated_count > 0:
             messagebox.showinfo("Calculation Complete", f"Calculated offline UUIDs for {calculated_count} player(s).\nThe table has been updated.")
        else:
             messagebox.showinfo("Calculation Complete", "No pending offline UUIDs found to calculate.")