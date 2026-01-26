# src/helpers.py
import hashlib
import uuid
import re
from .constants import BEDROCK_PREFIX_REGEX

def offline_uuid_from_name(name: str) -> str:
    # 🛠️ CORRECCIÓN #3: Blindaje de inputs (quitar espacios invisibles)
    clean_name = name.strip()
    
    m = hashlib.md5()
    m.update(("OfflinePlayer:" + clean_name).encode("utf-8"))
    return str(uuid.UUID(m.hexdigest()))

def format_uuid(raw_uuid: str) -> str:
    # CORRECCIÓN: .lower() es obligatorio para servidores Linux
    raw = (raw_uuid or "").strip().lower() 
    if len(raw) == 32:
        return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
    return raw

def find_worlds_in_dir(root_dir):
    worlds = []
    try:
        from .constants import TARGET_FOLDERS
        if any(os.path.isdir(os.path.join(root_dir, c)) for c in TARGET_FOLDERS):
            worlds.append(root_dir)
    except Exception:
        pass
    try:
        for entry in os.listdir(root_dir):
            p = os.path.join(root_dir, entry)
            if os.path.isdir(p) and any(os.path.isdir(os.path.join(p, c)) for c in TARGET_FOLDERS):
                worlds.append(p)
    except Exception:
        pass
    return worlds