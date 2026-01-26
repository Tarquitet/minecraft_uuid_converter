# main.py
import sys
import os

# Asegurarse de que el directorio src esté en el path de Python para imports relativos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importa la clase principal desde src
from src.app import UUIDConverterApp

def main():
    # Establecer DPI awareness en Windows para mejor escalado (opcional)
    try:
        if sys.platform == "win32":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass # Ignorar si no es Windows o falla

    # Importar la GUI (usando ttkbootstrap si está disponible)
    ttkbootstrap = None
    try:
        import ttkbootstrap
        root = ttkbootstrap.Window()
    except ImportError:
        import tkinter as tk
        root = tk.Tk()

    # Iniciar la aplicación
    app = UUIDConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()