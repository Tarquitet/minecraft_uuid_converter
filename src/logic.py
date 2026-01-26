# src/logic.py
import os
import shutil
import time # <-- Añadido para los timestamps
from .constants import TARGET_FOLDERS

def process_world(world_path, conversions, create_backup, log_fn, progress_callback=None):
    ops = 0
    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(world_path, folder)
        if not os.path.isdir(folder_path):
            log_fn(f"⚠ Folder missing: {folder_path}")
            continue
        try:
            for filename in os.listdir(folder_path):
                name_no_ext, ext = os.path.splitext(filename)
                copied_this_file = False 
                for player, uuid_from, uuid_to in conversions:
                    if copied_this_file: continue
                    if name_no_ext == uuid_from:
                        src = os.path.join(folder_path, filename)
                        dst = os.path.join(folder_path, f"{uuid_to}{ext}")
                        try:
                            if os.path.exists(dst):
                                if create_backup:
                                    # 🛠️ CORRECCIÓN #1: Backups con Timestamp único
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    bak_path = f"{dst}_{timestamp}.bak"
                                    if os.path.exists(bak_path):
                                        os.remove(bak_path)
                                    os.rename(dst, bak_path)
                                    log_fn(f"🛡️ Backup: {os.path.basename(dst)} -> {os.path.basename(bak_path)}")
                                else:
                                    os.remove(dst)
                                    log_fn(f"🗑️ Removed existing target: {os.path.basename(dst)}")
                            
                            shutil.copy2(src, dst)
                            log_fn(f"✅ {os.path.join(folder, filename)} -> {os.path.basename(dst)} (Copied)")
                            copied_this_file = True 
                            ops += 1
                        except Exception as e:
                            log_fn(f"❌ Error copying {src} -> {dst}: {e}")
                        
                        # 🛠️ CORRECCIÓN #4: Actualizar UI solo cada 50 archivos
                        if progress_callback and (ops % 50 == 0):
                            progress_callback()
        except Exception as e:
            log_fn(f"❌ Error scanning {folder_path}: {e}")
            
    # Asegurar que la barra llegue al 100% al terminar
    if progress_callback:
        progress_callback()
        
    return ops