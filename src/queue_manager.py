# src/queue_manager.py
import time
import queue
import tkinter as tk
from tkinter import messagebox

class QueueManager:
    def __init__(self, app_instance):
        self.app = app_instance

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.app.queue.get_nowait()
                if kind == "log":
                    self.app._append_log(payload)
                elif kind == "overall":
                    val = payload
                    self.app.overall_progress["value"] = min(self.app.overall_progress["maximum"], val)
                elif kind == "overall_max_adjust":
                     new_max = max(1, payload)
                     self.app.overall_progress["maximum"] = new_max
                     self.app.overall_progress["value"] = min(self.app.overall_progress["value"], new_max)
                elif kind == "add_usercache_row":
                    self.app.usercache_tv.insert("", "end", values=payload)
                elif kind == "add_playerdata_row":
                    self.app.playerdata_tv.insert("", "end", values=payload)
                elif kind == "update_world_status":
                    item_id, working_path, status = payload
                    try:
                        if self.app.items_tv.exists(item_id):
                             current = self.app.items_tv.item(item_id)['values']
                             self.app.items_tv.item(item_id, values=(current[0], current[1], working_path, status))
                    except Exception:
                        pass
                elif kind == "add_analysis_row":
                    iid = self.app.found_tv.insert("", "end", values=payload)
                    self.app.all_found_tv_items[iid] = payload
                    self.app.root.setvar(iid + "_values", payload)
                    self.app._update_analysis_counter()
                elif kind == "analysis_done":
                    players_found, item_id, working_path = payload
                    messagebox.showinfo("Analysis Complete",
                                f"Found {players_found} valid players. See Tab 4 for validated results.")
                    self.app.notebook.select(4)
                    self.app.queue.put(("update_world_status", (item_id, working_path, "Analyzed")))
                elif kind == "analysis_error":
                    error_msg, item_id = payload
                    messagebox.showerror("Analysis Error", str(error_msg))
                    self.app.queue.put(("update_world_status", (item_id, "Error", "Error")))
                elif kind == "analysis_error_validation":
                     error_msg, item_id = payload
                     messagebox.showerror("Validation Error!", str(error_msg))
                     self.app.queue.put(("update_world_status", (item_id, "Error", "Validation Error")))
                elif kind == "analysis_status_clear":
                    self.app.analyze_status_var.set("")
                elif kind == "update_analysis_table":
                    item_id, target_uuid, target_info = payload
                    try:
                        if self.app.found_tv.exists(item_id):
                            tk_var_name = item_id + "_values"
                            if not self.app.root.getvar(tk_var_name):
                                 self.app._append_log(f"Warning: TK variable {tk_var_name} not found for update (item might have been removed).")
                                 continue
                            original_payload = self.app.root.globalgetvar(tk_var_name)
                            if not isinstance(original_payload, (list, tuple)) or len(original_payload) != 5:
                                self.app._append_log(f"Warning: Invalid payload found in {tk_var_name}: {original_payload}")
                                continue
                            player, source_type, source_uuid, _, _ = original_payload
                            source_type_to_set = source_type
                            final_target_type = target_info
                            if isinstance(target_info, tuple) and len(target_info) == 2 and target_info[0] == "Already Online":
                                status, provider_name = target_info
                                final_target_type = "Already Online"
                                if provider_name == "Mojang":
                                    source_type_to_set = "Online (Mojang)"
                                elif provider_name == "Ely.by":
                                     source_type_to_set = "Online (Ely.by)"
                            elif not isinstance(target_info, str):
                                 final_target_type = str(target_info)
                            new_values = (
                                player,
                                source_type_to_set,
                                source_uuid,
                                final_target_type,
                                target_uuid
                            )
                            self.app.found_tv.item(item_id, values=new_values)
                            self.app.all_found_tv_items[item_id] = new_values
                            self.app.root.setvar(tk_var_name, new_values)
                    except Exception as e:
                        import traceback
                        self.app._append_log(f"ERROR in update_analysis_table for item {item_id}: {e}\n{traceback.format_exc()}")
                        pass
                elif kind == "done":
                    messagebox.showinfo("Done", "Processing finished.")
        except queue.Empty:
            pass
        self.app.root.after(150, self._poll_queue)

    def _append_log(self, text):
        ts = time.strftime("%H:%M:%S")
        try:
            self.app.log_text.config(state="normal")
            self.app.log_text.insert("end", f"[{ts}] {text}\n")
            self.app.log_text.see("end")
            self.app.log_text.config(state="disabled")
        except Exception:
            pass