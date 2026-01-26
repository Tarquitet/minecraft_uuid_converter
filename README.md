# WARNING - THIS IS ON BETA STATE

⛏️ Minecraft UUID Converter (GUI)

> **Una suite profesional de escritorio para migrar datos de jugadores (inventarios, estadísticas, logros y skins) entre diferentes tipos de UUID en servidores de Minecraft.**

**Minecraft UUID Converter** es una herramienta esencial para administradores de servidores. Permite realizar migraciones masivas y seguras de datos cuando un servidor cambia de modo (ej. Premium a No-Premium) o cuando se integran jugadores de Bedrock (GeyserMC) a Java. Todo esto a través de una interfaz gráfica moderna, rápida y segura.

![1769448117738](images/README/1769448117738.png)

![1769448123544](images/README/1769448123544.png)

![1769448132179](images/README/1769448132179.png)

![1769448140458](images/README/1769448140458.png)

## ✨ Características Principales

- **🔄 Conversión Bidireccional:** Soporta migraciones de Online (Premium) a Offline (Cracked), y resolución de conflictos entre cuentas de Java y Bedrock (Geyser).
- **🧠 Auto-Cálculo de UUIDs Offline:** El algoritmo integrado genera instantáneamente los UUIDs correctos para el modo "No-Premium" usando el estándar de Mojang (MD5 de `OfflinePlayer:Nombre`).
- **🛡️ Sistema de Backup Automático:** Nunca perderás datos. El script genera copias de seguridad (`.bak`) de los archivos originales antes de sobrescribirlos.
- **⚡ Multihilo (Anti-Congelamiento):** La interfaz gráfica nunca se congela. El análisis profundo y la conversión de archivos ocurren en segundo plano utilizando `QueueManager` y `Threading`.
- **📦 Auto-Instalador:** No requiere configuración compleja. Al ejecutar el programa por primera vez, detectará e instalará automáticamente las dependencias faltantes (`ttkbootstrap`, `requests`).

---

## ⚙️ Requisitos e Instalación

**Requisitos del sistema:**

- Python 3.8 o superior.
- Acceso a la carpeta del mundo del servidor (ej. `world/`) y al archivo `usercache.json`.

**Dependencias (gestionadas automáticamente):**

- `ttkbootstrap` (Para el tema moderno y oscuro).
- `requests` (Para consultas a la API de Mojang).

### Ejecución

```bash
python main.py
```

📖 Guía de Uso (Flujo de 5 Pasos)

La interfaz está dividida en pestañas que te guían paso a paso:

🏁 Intro & Mode: Selecciona el modo de conversión (ej. Online a Offline).

📂 World Selection: Carga la carpeta de tu mundo (ej. C:/servidor/world) y tu archivo usercache.json.

🔍 Usercache: Revisa la lista de jugadores detectados en la caché del servidor.

🗺️ UUID Mapping (El cerebro): Aquí verás el análisis. Selecciona los jugadores y usa el botón "Calculate Offline UUIDs" para que el script determine a qué archivos renombrar los datos.

🚀 Convert: Revisa el resumen final y presiona Start Conversion. Los archivos se copiarán con sus nuevos nombres instantáneamente.
📂 ¿Qué datos se convierten?

El script busca y renombra archivos de forma segura en las siguientes subcarpetas del mundo:

playerdata/ (Inventarios, posición, salud, Enderchest)

stats/ (Estadísticas de minado, muertes, tiempo de juego)

advancements/ (Logros desbloqueados)

skinrestorer/ (Datos del plugin de skins, si existe)
🏗️ Arquitectura del Código

El proyecto sigue una arquitectura modular y limpia para facilitar su mantenimiento:

main.py: Punto de entrada y configuración de DPI para Windows.

app.py: Controlador principal de la GUI.

logic.py: Motor de conversión de archivos (I/O).

queue_manager.py: Sistema de cola para actualizar la UI desde hilos de trabajo.

ui_builder.py / ui_components.py: Construcción de widgets y temas (Treeviews, Tabs).

# TO-DO

## ⚙️ Notas Técnicas y Optimizaciones (V2)

Esta herramienta está diseñada con arquitectura de "Grado de Producción" para evitar cuelgues del servidor y corrupción de datos.

- **🐧 Compatibilidad estricta con Linux:** A diferencia de Windows, los servidores Linux distinguen entre mayúsculas y minúsculas (Case-Sensitive). El algoritmo fuerza que todos los UUIDs renombrados estén en minúsculas estrictas para asegurar que el servidor los lea correctamente.
- **🛡️ Backups Aislados (Anti-Corrupción):** Los archivos de seguridad no se mezclan con los datos del juego. Se genera una subcarpeta independiente (`/uuid_backups/`) y se utilizan _Timestamps_ (marcas de tiempo) para que múltiples conversiones no sobrescriban los historiales.
- **🚀 Anti-Congelamiento de RAM (Event Loop Limit):** Para servidores masivos con archivos `usercache.json` de más de 50,000 líneas, la interfaz gráfica limita el renderizado visual a los últimos 2,000 jugadores activos, mientras que el "Backend" procesa el 100% de los datos en segundo plano usando Multi-threading.

---

## 📱 Consideraciones para GeyserMC (Jugadores Bedrock)

El script detecta automáticamente a los jugadores de Bedrock gracias a sus prefijos (ej. `*UsuarioBedrock` o `.UsuarioBedrock`).

**⚠️ Importante sobre la Fusión de Cuentas (Bedrock a Java):**
Al realizar la conversión de "Bedrock a Java", el script **elimina el prefijo** para buscar el UUID de la cuenta de PC. Esto tiene dos efectos según tu objetivo:

1. **Fusión (Recomendado):** Si el jugador de móvil ahora jugará en PC, su inventario se fusionará limpiamente con la cuenta de Java.
2. **Independencia:** Si el jugador seguirá jugando en móvil, GeyserMC podría no reconocer el nuevo archivo sin el prefijo. (Se recomienda realizar pruebas en la carpeta de trabajo primero).

---

## 🔮 Roadmap y Limitaciones Conocidas (Soporte NBT)

Actualmente, el script realiza la migración a **"Nivel de Sistema de Archivos"** (File-level renaming). Cambia el nombre del archivo de `UUID-A.dat` a `UUID-B.dat`.

Para servidores en **Minecraft 1.19 e inferiores**, esto funciona perfectamente.

**Limitación para Minecraft 1.20.5+:**
Las versiones más recientes son más estrictas. Dentro del archivo `.dat` existe una estructura binaria (Named Binary Tag) que también guarda el UUID internamente. A veces, si el nombre del archivo no coincide con el UUID interno, el servidor regenera el inventario a cero.

**Próximos pasos (Futura Actualización):**

- Integración con la librería `nbtlib` de Python para abrir el archivo binario, localizar la etiqueta `UUID: [I; x, x, x, x]` interna y modificarla directamente, asegurando una compatibilidad nativa total con las versiones 1.21+.

# FINAL TO-DO

- [ ] **Nota GeyserMC (Bedrock):** Advertir que el modo "Bedrock a Java" quita el prefijo y fusiona inventarios con cuentas de PC.
- [ ] **Compatibilidad Linux:** Mencionar que se fuerzan las minúsculas en los nombres de archivo para que los servidores Linux no pierdan los datos.
- [ ] **Backups Aislados:** Explicar que las copias de seguridad ahora van a `/uuid_backups/` con fecha/hora para no saturar la carpeta principal.
- [ ] **Rendimiento (Anti-Lag):** Indicar que la interfaz solo muestra 2,000 jugadores para evitar cuelgues, pero el script procesa el 100% en segundo plano.
- [ ] **Roadmap 1.20.5+:** Añadir que en el futuro se implementará `nbtlib` para modificar el UUID interno del archivo (solución definitiva para las últimas versiones).

---

⚖️ Licencia

Este proyecto es de uso libre para la comunidad de administradores de servidores de Minecraft.
