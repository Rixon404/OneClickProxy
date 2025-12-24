#!/usr/bin/env python3
"""
Main entry point for Proxy Manager
"""
try:
    import customtkinter as ctk
except ImportError:
    print("Error: customtkinter no está instalado. Instala con: pip install customtkinter")
    raise
import sys
import time
from proxy_manager.config.settings import ConfigManager
from proxy_manager.models.proxy_manager import ProxyModel
from proxy_manager.ui.main_window import MainWindow
from proxy_manager.controllers.main_controller import MainController


def main():
    """Main application entry point"""
    print("=== INICIANDO PROXY MANAGER ===")
    print(f"Python version: {sys.version}")
    print(f"CustomTkinter version: {ctk.__version__ if hasattr(ctk, '__version__') else 'desconocida'}")
    
    # Initialize application components
    config_manager = ConfigManager()
    proxy_model = ProxyModel(config_manager)
    
    # Create controller and view
    view = MainWindow(None)  # Pass None initially
    controller = MainController(config_manager, proxy_model, view)
    
    # Now set the controller in the view
    view.controller = controller
    
    try:
        view.run()
    except Exception as e:
        print(f"Error fatal en mainloop: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("✅ CustomTkinter importado correctamente")
    main()