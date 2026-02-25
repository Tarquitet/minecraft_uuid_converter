# WARNING - THIS IS ON BETA STATE

[Read in English (README.md)](README.md)

⛏️ Minecraft UUID Converter (GUI)

> **Una suite profesional de escritorio para migrar datos de jugadores (inventarios, estadísticas, logros y skins) entre diferentes tipos de UUID en servidores de Minecraft.**

**Minecraft UUID Converter** es una herramienta esencial para administradores de servidores. Permite realizar migraciones masivas y seguras de datos cuando un servidor cambia de modo (ej. Premium a No-Premium) o cuando se integran jugadores de Bedrock (GeyserMC) a Java. Todo esto a través de una interfaz gráfica moderna, rápida y segura.

![1769448117738](images/README/1769448117738.png)
![1769448123544](images/README/1769448123544.png)
![1769448132179](images/README/1769448132179.png)
![1769448140458](images/README/1769448140458.png)

## ✨ Características Principales

- **🔄 Conversión Bidireccional:** Soporta migraciones de Online (Premium) a Offline (Cracked), y resolución de conflictos entre cuentas de Java y Bedrock (Geyser).
- **🧠 Auto-Cálculo de UUIDs Offline:** Genera los UUIDs correctos usando el estándar de Mojang (MD5 de `OfflinePlayer:Nombre`).
- **✏️ Mapeo y Edición Manual:** Edita el UUID de destino manualmente para transferir progresos entre cuentas o corregir errores.
- **🛡️ Sistema de Backup Aislado:** Si detecta una colisión de nombres, envía el archivo antiguo a `/uuid_backups/` con un _timestamp_ para evitar sobrescrituras accidentales.
- **⚡ Multihilo y Optimizado:** La interfaz nunca se congela. El motor procesa el 100% de la base de datos en segundo plano mientras que la GUI se mantiene fluida limitando la vista previa a los 2,000 registros más recientes.
- **📦 Auto-Instalador:** Detecta e instala automáticamente las dependencias faltantes (`ttkbootstrap`, `requests`) al ejecutar el programa.

---

## ⚙️ Requisitos e Instalación

**Requisitos del sistema:**

- Python 3.8 o superior.
- Acceso a la carpeta del mundo del servidor (ej. `world/`) y al archivo `usercache.json`.
- **Usuarios de Linux:** Es posible que necesites instalar: `sudo apt install python3-tk`.

**Dependencias (gestionadas automáticamente):**

- `ttkbootstrap` (Para el tema moderno).
- `requests` (Para consultas a la API de Mojang y Ely.by).

### Ejecución

```bash
python main.py

```

---

## 📖 Guía de Uso (Flujo de 5 Pasos)

1. 🏁 **Intro & Mode:** Selecciona el modo (ej. Offline -> Online) para que el script sepa qué UUIDs buscar.
2. 📂 **World Selection:** Carga la carpeta de tu mundo y asigna el archivo `usercache.json`.
3. 🔍 **Usercache:** Revisa los datos crudos detectados en la caché.
4. 🗺️ **UUID Mapping (El cerebro):** Selecciona jugadores y usa `Search Online` o edita manualmente sus destinos. Puedes importar/exportar mapeos en formato `.json`.
5. 🚀 **Convert:** Revisa el plan final y presiona `Start Conversion`. El script creará una copia procesada en la carpeta `converted_worlds`.

---

## 📝 Notas Técnicas y Documentación

### 🐧 Compatibilidad y Seguridad en Linux

El script fuerza un renombrado estricto respetando las minúsculas y mayúsculas (Case-Sensitive), previniendo errores al migrar datos hacia servidores Linux.

### ⚡ Optimización Anti-Lag (Protección de RAM)

Para servidores con miles de jugadores, la GUI limita la visualización a los **2,000 jugadores** más recientes para proteger la RAM. Sin embargo, el motor procesa y migra el **100% de los archivos** del mundo.

### ⚠️ Advertencia sobre GeyserMC (Bedrock a Java)

Al convertir cuentas de Bedrock, el script limpia automáticamente prefijos como `.` o `*`.

- **Ventaja:** Ideal para fusionar el progreso de un jugador móvil que compró la versión de PC.
- **Nota Crítica:** Si el jugador sigue entrando desde Bedrock, esta migración "desconectará" su inventario de su cuenta móvil original.

### 🌐 Límites de búsqueda Online

La función `Search Online` hace peticiones reales a las APIs. Si escaneas cientos de jugadores a la vez, el proceso puede tardar unos segundos para evitar bloqueos por exceso de peticiones.

---

⚖️ **Licencia**
Este proyecto es de uso libre para la comunidad de administradores de servidores de Minecraft.
**Autor:** Tarquitet.
