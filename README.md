---

### 🇺🇸 File: `README.md` (Main English Version)


# WARNING - THIS IS ON BETA STATE

[Leer en Español (README_ES.md)](README_ES.md)

⛏️ Minecraft UUID Converter (GUI)

> **A professional desktop suite for migrating player data (inventories, stats, advancements, and skins) between different UUID types on Minecraft servers.**

**Minecraft UUID Converter** is an essential tool for server administrators. It enables secure, bulk data migrations when a server changes modes (e.g., Premium to Non-Premium) or when integrating Bedrock (GeyserMC) players into Java. All of this is performed through a modern, fast, and secure graphical interface.

![1769448117738](images/README/1769448117738.png)
![1769448123544](images/README/1769448123544.png)
![1769448132179](images/README/1769448132179.png)
![1769448140458](images/README/1769448140458.png)

## ✨ Main Features

- **🔄 Bidirectional Conversion:** Supports migrations from Online (Premium) to Offline (Cracked), and resolves conflicts between Java and Bedrock (Geyser) accounts.
- **🧠 Auto-Calculation of Offline UUIDs:** Instantly generates the correct UUIDs using the Mojang standard (MD5 of `OfflinePlayer:Name`).
- **✏️ Manual Mapping & Editing:** Allows manual editing of the target UUID to transfer progress between different accounts or correct detection errors.
- **🛡️ Isolated Backup System:** If a name collision is detected, the script moves the old file to a `/uuid_backups/` subfolder with a timestamp to prevent accidental overwrites.
- **⚡ Multithreaded & Optimized:** The interface never freezes. The engine processes 100% of the database in the background, while the GUI remains fluid by limiting the preview to the 2,000 most recent records.
- **📦 Auto-Installer:** Automatically detects and installs missing dependencies (`ttkbootstrap`, `requests`) upon execution.

---

## ⚙️ Requirements and Installation

**System Requirements:**

- Python 3.8 or higher.
- Access to the server world folder (e.g., `world/`) and the `usercache.json` file.
- **Linux Users:** You may need to install the graphical interface library manually: `sudo apt install python3-tk`.

**Dependencies (managed automatically):**

- `ttkbootstrap` (For the modern theme).
- `requests` (For Mojang and Ely.by API queries).

### Execution

```bash
python main.py
```

````

---

## 📖 Usage Guide (5-Step Flow)

1. 🏁 **Intro & Mode:** Select the mode (e.g., Offline -> Online) so the script knows which UUIDs to search for.
2. 📂 **World Selection:** Load your world folder and assign the `usercache.json` file.
3. 🔍 **Usercache:** Review the raw data detected in the cache.
4. 🗺️ **UUID Mapping (The Brain):** Select players and use `Search Online` or manually edit their destinations. You can import/export mappings in `.json` format here.
5. 🚀 **Convert:** Review the final plan and press `Start Conversion`. The script will create a processed copy in the `converted_worlds` folder.

---

## 📝 Technical Notes and Documentation

### 🐧 Linux Compatibility and Security

The script forces strict renaming, respecting case-sensitivity, preventing reading errors when migrating data to Linux-hosted servers.

### ⚡ Anti-Lag Optimization (RAM Protection)

When analyzing servers with thousands of players, the GUI limits the display to the **2,000 most recent players** to protect system RAM. However, the logical engine processes and migrates **100% of the files** found in the world folder.

### ⚠️ Warning about GeyserMC (Bedrock to Java)

When converting Bedrock accounts, the script automatically cleans common prefixes like `.` or `*`.

- **Advantage:** Ideal for merging progress of a mobile player who purchased the PC version.
- **Critical Note:** If the player intends to continue joining from Bedrock, this migration will "disconnect" their inventory from their original mobile account.

### 🌐 Online Search Limits

The `Search Online` function makes real requests to Mojang and Ely.by APIs. If you scan hundreds of players simultaneously, the process may take a few seconds to avoid API rate-limiting.

---

⚖️ **License**
This project is free to use for the Minecraft server administrator community.
**Author:** Tarquitet.

```

```
````
