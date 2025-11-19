#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import os
import json
from pathlib import Path
import tempfile
import time
import sys

class ProxyManagerApp:
    def __init__(self):
        # Configuracion de customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Proxy Manager - Ubuntu")
        self.root.geometry("500x620")
        self.root.resizable(False, False)
        
        # Variables de estado
        self.proxy_active = False
        self.services_active = True
        self.admin_password_cache = None  # Almacenar contraseña temporalmente
        
        # Cargar credenciales y configuracion
        self.credentials = self.load_credentials()
        self.config_file = Path.home() / ".proxy_manager_config.json"
        self.proxy_settings = self.load_config()
        
        self.create_widgets()
        self.check_proxy_status()
        self.check_services_status()
        
    def load_credentials(self):
        """Cargar credenciales guardadas"""
        credentials_file = Path.home() / ".proxy_manager_credentials.json"
        default_creds = {"username": "", "password": ""}
        
        if credentials_file.exists():
            try:
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando credenciales: {e}")
                return default_creds
        else:
            with open(credentials_file, 'w') as f:
                json.dump(default_creds, f, indent=2)
            return default_creds
    
    def save_credentials(self):
        """Guardar credenciales"""
        credentials_file = Path.home() / ".proxy_manager_credentials.json"
        try:
            with open(credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
        except Exception as e:
            print(f"Error guardando credenciales: {e}")
    
    def load_config(self):
        """Cargar configuracion de proxy guardada o usar valores por defecto"""
        default_config = {
            "http_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "https_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "ftp_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "no_proxy": "localhost,127.0.0.1,localaddress,.localdomain.com,*.cu",
            "apt_proxy": "http://usuario:contraseña@192.168.91.20:3128"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando configuracion: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config):
        """Guardar configuracion de proxy"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error guardando configuracion: {e}")
    
    def create_widgets(self):
        """Crear la interfaz de usuario"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Titulo
        title_label = ctk.CTkLabel(
            main_frame, 
            text="GESTOR DE PROXY Y USB", 
            font=("Arial", 24, "bold"),
            text_color="#3498db"
        )
        title_label.pack(pady=(10, 5))
        
        # Subtitulo
        subtitle_label = ctk.CTkLabel(
            main_frame, 
            text="Control total con un clic",
            font=("Arial", 14)
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Frame para credenciales
        credentials_frame = ctk.CTkFrame(main_frame)
        credentials_frame.pack(padx=20, pady=10, fill="x")
        
        # Etiqueta y campo de usuario
        user_frame = ctk.CTkFrame(credentials_frame)
        user_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(user_frame, text="Usuario:", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        self.user_entry = ctk.CTkEntry(user_frame, width=200)
        self.user_entry.insert(0, self.credentials["username"])
        self.user_entry.pack(side="left", padx=5)
        
        # Etiqueta y campo de contrasena
        pass_frame = ctk.CTkFrame(credentials_frame)
        pass_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(pass_frame, text="Contrasena:", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        self.pass_entry = ctk.CTkEntry(pass_frame, show="*", width=200)
        self.pass_entry.insert(0, self.credentials["password"])
        self.pass_entry.pack(side="left", padx=5)
        
        # Boton para mostrar/ocultar contrasena
        self.show_pass_var = ctk.BooleanVar()
        self.show_pass_btn = ctk.CTkCheckBox(pass_frame, text="Mostrar", variable=self.show_pass_var, 
                                            command=self.toggle_password_visibility)
        self.show_pass_btn.pack(side="right", padx=(5, 10))
        
        # Frame para botones de credenciales (horizontal)
        creds_btn_frame = ctk.CTkFrame(credentials_frame)
        creds_btn_frame.pack(pady=10, fill="x")
        
        # Boton para guardar credenciales - color azul #3498db
        save_creds_btn = ctk.CTkButton(creds_btn_frame, text="💾 Guardar Credenciales", 
                                      command=self.save_current_credentials,
                                      fg_color="#3498db",  # Mismo azul que el titulo
                                      text_color="white",  # Texto blanco
                                      hover_color="#2980b9",  # Azul mas oscuro para hover
                                      height=30)
        save_creds_btn.pack(side="left", padx=(20, 10), pady=5)
        
        # Boton para actualizar contrasena en todos los proxies - color azul #3498db
        update_pass_btn = ctk.CTkButton(creds_btn_frame, text="🔄 Actualizar Contraseña", 
                                       command=self.update_all_proxies_password,
                                       fg_color="#3498db",  # Mismo azul que el titulo
                                       text_color="white",  # Texto blanco
                                       hover_color="#2980b9",  # Azul mas oscuro para hover
                                       height=30)
        update_pass_btn.pack(side="left", padx=(10, 20), pady=5)
        
        # Frame para el boton dinamico de proxy
        proxy_button_frame = ctk.CTkFrame(main_frame)
        proxy_button_frame.pack(padx=20, pady=10, fill="x")
        
        # Unico boton dinamico para proxy
        self.proxy_btn = ctk.CTkButton(
            proxy_button_frame,
            text="✅ ACTIVAR PROXY",
            font=("Arial", 16, "bold"),
            fg_color="#006400",
            hover_color="#228B22",
            height=60,
            command=self.toggle_proxy
        )
        self.proxy_btn.pack(padx=20, pady=10, fill="x")
        
        # Estado actual del proxy
        self.proxy_status_label = ctk.CTkLabel(
            main_frame,
            text="Estado Proxy: ❌ DESACTIVADO", 
            font=("Arial", 14, "bold"),
            text_color="#e74c3c"
        )
        self.proxy_status_label.pack(pady=5)
        
        # Seccion para control de servicios USB
        usb_frame = ctk.CTkFrame(main_frame)
        usb_frame.pack(padx=20, pady=15, fill="x")
        
        usb_title = ctk.CTkLabel(
            usb_frame,
            text="CONTROL DE MEMORIAS USB",
            font=("Arial", 16, "bold"),
            text_color="#3498db"
        )
        usb_title.pack(pady=(10, 5))
        
        usb_subtitle = ctk.CTkLabel(
            usb_frame,
            text="Detener servicios de Kaspersky para usar memorias USB",
            font=("Arial", 11),
            text_color="#95a5a6"
        )
        usb_subtitle.pack(pady=(0, 10))
        
        # Boton dinamico para servicios - MAS GRANDE!
        self.usb_btn = ctk.CTkButton(
            usb_frame,
            text="🔌 DETENER SERVICIOS PARA USB",
            font=("Arial", 14, "bold"),
            fg_color="#8B0000",
            hover_color="#A0522D",
            height=65,
            command=self.toggle_usb_services
        )
        self.usb_btn.pack(padx=20, pady=15, fill="x")
        
        # Estado actual de servicios
        self.usb_status_label = ctk.CTkLabel(
            usb_frame,
            text="Estado Servicios: ✅ ACTIVOS", 
            font=("Arial", 12, "bold"),
            text_color="#2ecc71"
        )
        self.usb_status_label.pack(pady=(0, 15))
        
        # Boton de configuracion
        config_btn = ctk.CTkButton(
            main_frame,
            text="⚙️ Configurar Proxy",
            font=("Arial", 12),
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            height=30,
            command=self.open_config_window
        )
        config_btn.pack(pady=10)
        
        # Indicador de permisos
        self.sudo_label = ctk.CTkLabel(
            main_frame,
            text="🔒 Se necesitaran permisos de administrador para ambas operaciones",
            font=("Arial", 10),
            text_color="#f39c12"
        )
        self.sudo_label.pack(pady=(5, 15))
    
    def toggle_password_visibility(self):
        """Mostrar u ocultar la contrasena"""
        if self.show_pass_var.get():
            self.pass_entry.configure(show="")
        else:
            self.pass_entry.configure(show="*")
    
    def save_current_credentials(self):
        """Guardar las credenciales actuales"""
        self.credentials["username"] = self.user_entry.get()
        self.credentials["password"] = self.pass_entry.get()
        self.save_credentials()
        self.show_success("✅ Credenciales guardadas correctamente")
    
    def update_all_proxies_password(self):
        """Actualizar la contraseña en todos los proxies del sistema sin reiniciar"""
        try:
            self.usb_status_label.configure(text="Estado: ⏳ Actualizando contraseñas...", text_color="#f39c12")
            self.root.update_idletasks()
            time.sleep(0.1)
            
            # Usar contraseña cacheada o solicitarla
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password  # Guardar en cache
            
            if not password:
                self.show_error("❌ Operacion cancelada por el usuario")
                return
            
            # Actualizar credenciales en la configuracion
            username = self.user_entry.get()
            new_password = self.pass_entry.get()
            
            if not username or not new_password:
                self.show_error("❌ Usuario y contraseña no pueden estar vacios")
                return
            
            # Actualizar la configuracion de proxy con las nuevas credenciales
            updated_count = 0
            for key in ['http_proxy', 'https_proxy', 'ftp_proxy', 'apt_proxy']:
                if key in self.proxy_settings:
                    current_url = self.proxy_settings[key]
                    if '://' in current_url:
                        protocol = current_url.split('://')[0]
                        rest = current_url.split('://')[1]
                        if '@' in rest:
                            host_port = rest.split('@')[1]
                            self.proxy_settings[key] = f"{protocol}://{username}:{new_password}@{host_port}"
                        else:
                            self.proxy_settings[key] = f"{protocol}://{username}:{new_password}@{rest}"
                    updated_count += 1
            
            # Guardar la configuracion actualizada
            self.save_config(self.proxy_settings)
            
            # Actualizar /etc/environment
            env_content = f"""
# Proxy Settings - Actualizado por Proxy Manager
http_proxy="{self.proxy_settings['http_proxy']}"
https_proxy="{self.proxy_settings['https_proxy']}"
ftp_proxy="{self.proxy_settings['ftp_proxy']}"
no_proxy="{self.proxy_settings['no_proxy']}"
HTTP_PROXY="{self.proxy_settings['http_proxy']}"
HTTPS_PROXY="{self.proxy_settings['https_proxy']}"
FTP_PROXY="{self.proxy_settings['ftp_proxy']}"
NO_PROXY="{self.proxy_settings['no_proxy']}"
"""
            
            # Escribir el nuevo contenido para /etc/environment
            success_env, stdout_env, stderr_env = self.run_command_with_sudo(
                f"echo '{env_content}' > /etc/environment", 
                password
            )
            
            # Actualizar proxy para apt
            apt_config = f"""
# Proxy Settings - Actualizado por Proxy Manager
Acquire::http::proxy "{self.proxy_settings['apt_proxy']}/";
Acquire::https::proxy "{self.proxy_settings['apt_proxy']}/";
Acquire::ftp::proxy "{self.proxy_settings['apt_proxy']}/";
"""
            
            # Escribir el nuevo contenido para apt
            success_apt, stdout_apt, stderr_apt = self.run_command_with_sudo(
                f"echo '{apt_config}' > /etc/apt/apt.conf.d/99proxy && chmod 644 /etc/apt/apt.conf.d/99proxy", 
                password
            )
            
            if success_env and success_apt:
                # Mostrar variables de entorno actualizadas en la sesion actual
                env_commands = [
                    f'export http_proxy="{self.proxy_settings["http_proxy"]}"',
                    f'export https_proxy="{self.proxy_settings["https_proxy"]}"',
                    f'export ftp_proxy="{self.proxy_settings["ftp_proxy"]}"',
                    f'export no_proxy="{self.proxy_settings["no_proxy"]}"',
                    f'export HTTP_PROXY="{self.proxy_settings["http_proxy"]}"',
                    f'export HTTPS_PROXY="{self.proxy_settings["https_proxy"]}"',
                    f'export FTP_PROXY="{self.proxy_settings["ftp_proxy"]}"',
                    f'export NO_PROXY="{self.proxy_settings["no_proxy"]}"'
                ]
                
                for cmd in env_commands:
                    try:
                        subprocess.run(cmd, shell=True, executable='/bin/bash', timeout=5)
                    except Exception as e:
                        print(f"Advertencia al actualizar variable de entorno: {e}")
                
                self.show_success(f"✅ ¡Contraseñas actualizadas correctamente en {updated_count} proxies!\nNo es necesario reiniciar el proxy")
            else:
                error_msg = "❌ Error al actualizar archivos de configuracion"
                if not success_env:
                    error_msg += f"\n/etc/environment: {stderr_env}"
                if not success_apt:
                    error_msg += f"\nAPT config: {stderr_apt}"
                self.show_error(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
        finally:
            self.usb_status_label.configure(text="Estado Servicios: ✅ ACTIVOS", text_color="#2ecc71")
    
    def check_proxy_status(self):
        """Verificar el estado actual del proxy"""
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.system.proxy', 'mode'], 
                                  capture_output=True, text=True, timeout=5)
            mode = result.stdout.strip().strip("'")
            
            self.proxy_active = (mode == 'manual')
            self.update_proxy_status_display()
            
        except Exception as e:
            error_msg = f"Error al verificar proxy: {str(e)}"
            print(error_msg)
            self.proxy_status_label.configure(text=f"Error: {str(e)}", text_color="#e74c3c")
    
    def check_services_status(self):
        """Verificar el estado de los servicios de Kaspersky"""
        try:
            services = ["klnagent64", "klnagent64.service"]
            all_active = True
            
            for service in services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True, timeout=5)
                    if result.stdout.strip() != "active":
                        all_active = False
                        break
                except subprocess.TimeoutExpired:
                    print(f"Timeout verificando servicio {service}")
                    all_active = False
                    break
            
            self.services_active = all_active
            self.update_services_status_display()
            
        except Exception as e:
            print(f"Error verificando servicios: {e}")
            self.services_active = True
    
    def update_proxy_status_display(self):
        """Actualizar el estado mostrado del proxy"""
        if self.proxy_active:
            self.proxy_status_label.configure(
                text="Estado Proxy: ✅ ACTIVO", 
                text_color="#2ecc71"
            )
            self.proxy_btn.configure(
                text="❌ DESACTIVAR PROXY",
                fg_color="#8B0000",
                hover_color="#A0522D",
                state="normal"
            )
        else:
            self.proxy_status_label.configure(
                text="Estado Proxy: ❌ DESACTIVADO", 
                text_color="#e74c3c"
            )
            self.proxy_btn.configure(
                text="✅ ACTIVAR PROXY",
                fg_color="#006400",
                hover_color="#228B22",
                state="normal"
            )
    
    def update_services_status_display(self):
        """Actualizar el estado mostrado de los servicios"""
        if self.services_active:
            self.usb_status_label.configure(
                text="Estado Servicios: ✅ ACTIVOS", 
                text_color="#2ecc71"
            )
            self.usb_btn.configure(
                text="🔌 DETENER SERVICIOS PARA USB",
                fg_color="#8B0000",
                hover_color="#A0522D",
                state="normal"
            )
        else:
            self.usb_status_label.configure(
                text="Estado Servicios: ❌ DETENIDOS", 
                text_color="#e74c3c"
            )
            self.usb_btn.configure(
                text="✅ ACTIVAR SERVICIOS PARA USB",
                fg_color="#006400",
                hover_color="#228B22",
                state="normal"
            )
    
    def ask_sudo_password(self):
        """Solicitar contrasena de administrador de forma segura"""
        try:
            # Si ya tenemos una contraseña en cache, usarla
            if self.admin_password_cache:
                return self.admin_password_cache
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Contrasena de administrador")
            dialog.geometry("350x180")
            
            # Centrar el dialogo
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 350) // 2
            y = (screen_height - 180) // 2
            dialog.geometry(f"+{x}+{y}")
            
            dialog.update_idletasks()
            time.sleep(0.1)
            
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.focus_force()
            
            frame = ctk.CTkFrame(dialog)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(frame, text="Introduce tu contrasena de administrador:", 
                        font=("Arial", 12)).pack(pady=10)
            
            password_entry = ctk.CTkEntry(frame, show="*", width=300)
            password_entry.pack(pady=10)
            password_entry.focus()
            
            result = [None]
            
            def confirm():
                result[0] = password_entry.get()
                dialog.destroy()
            
            def cancel():
                result[0] = None
                dialog.destroy()
            
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.pack(pady=10)
            
            ctk.CTkButton(btn_frame, text="Aceptar", command=confirm, 
                         fg_color="#2ecc71", width=100).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Cancelar", command=cancel, 
                         fg_color="#e74c3c", width=100).pack(side="left", padx=5)
            
            password_entry.bind('<Return>', lambda e: confirm())
            
            self.root.wait_window(dialog)
            
            # Almacenar en cache si se proporciona una contraseña valida
            if result[0]:
                self.admin_password_cache = result[0]
            
            return result[0]
            
        except Exception as e:
            print(f"Error creando dialogo de contrasena: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_command_with_sudo(self, command, password):
        """Ejecutar comando con sudo usando la contrasena"""
        if not password:
            return False, "", "Contrasena vacia"
        
        cmd = f"echo '{password}' | sudo -S {command}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def toggle_proxy(self):
        """Alternar entre activar y desactivar proxy"""
        try:
            if self.proxy_active:
                self.disable_proxy()
            else:
                self.enable_proxy()
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
    
    def enable_proxy(self):
        """Activar proxy"""
        try:
            self.proxy_status_label.configure(text="Estado Proxy: ⏳ Activando...", text_color="#f39c12")
            self.proxy_btn.configure(state="disabled")
            self.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.show_error("❌ Operacion cancelada por el usuario")
                self.update_proxy_status_display()
                return
            
            self.update_proxy_settings_with_credentials()
            success = self._perform_enable_proxy(password)
            
            if success:
                self.proxy_active = True
                self.update_proxy_status_display()
                self.show_success("✅ ¡Proxy activado correctamente!")
            else:
                self.show_error("❌ Error al activar el proxy. Revisa la terminal para mas detalles.")
                self.update_proxy_status_display()
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
            self.update_proxy_status_display()
        finally:
            self.proxy_btn.configure(state="normal")
    
    def disable_proxy(self):
        """Desactivar proxy"""
        try:
            self.proxy_status_label.configure(text="Estado Proxy: ⏳ Desactivando...", text_color="#f39c12")
            self.proxy_btn.configure(state="disabled")
            self.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.show_error("❌ Operacion cancelada por el usuario")
                self.update_proxy_status_display()
                return
            
            success = self._perform_disable_proxy(password)
            
            if success:
                self.proxy_active = False
                self.update_proxy_status_display()
                self.show_success("✅ ¡Proxy desactivado correctamente!")
            else:
                self.show_error("❌ Error al desactivar el proxy. Revisa la terminal para mas detalles.")
                self.update_proxy_status_display()
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
            self.update_proxy_status_display()
        finally:
            self.proxy_btn.configure(state="normal")
    
    def toggle_usb_services(self):
        """Alternar entre detener y activar servicios USB"""
        try:
            if self.services_active:
                self.stop_usb_services()
            else:
                self.start_usb_services()
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
    
    def stop_usb_services(self):
        """Detener servicios de Kaspersky para USB"""
        try:
            self.usb_status_label.configure(text="Estado Servicios: ⏳ Deteniendo...", text_color="#f39c12")
            self.usb_btn.configure(state="disabled")
            self.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.show_error("❌ Operacion cancelada por el usuario")
                self.update_services_status_display()
                return
            
            print("=== DETENIENDO SERVICIOS PARA USB ===")
            
            services = ["klnagent64.service", "klnagent64"]
            all_success = True
            
            for service in services:
                print(f"Deteniendo servicio: {service}")
                success, stdout, stderr = self.run_command_with_sudo(f"systemctl stop {service}", password)
                
                if success:
                    print(f"✓ Servicio {service} detenido correctamente")
                else:
                    print(f"❌ Error deteniendo {service}: {stderr}")
                    all_success = False
            
            # Verificar estado real despues de detener
            time.sleep(1)
            self.check_services_status()
            
            if all_success and not self.services_active:
                self.show_success("✅ ¡Servicios detenidos correctamente!\nAhora puedes conectar memorias USB")
            else:
                self.show_error("❌ Error al detener servicios. Revisa la terminal para detalles.")
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
        finally:
            self.usb_btn.configure(state="normal")
            self.check_services_status()
    
    def start_usb_services(self):
        """Activar servicios de Kaspersky para USB"""
        try:
            self.usb_status_label.configure(text="Estado Servicios: ⏳ Activando...", text_color="#f39c12")
            self.usb_btn.configure(state="disabled")
            self.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.show_error("❌ Operacion cancelada por el usuario")
                self.update_services_status_display()
                return
            
            print("=== ACTIVANDO SERVICIOS PARA USB ===")
            
            services = ["klnagent64", "klnagent64.service"]
            all_success = True
            
            for service in services:
                print(f"Activando servicio: {service}")
                success, stdout, stderr = self.run_command_with_sudo(f"systemctl start {service}", password)
                
                if success:
                    print(f"✓ Servicio {service} activado correctamente")
                else:
                    print(f"❌ Error activando {service}: {stderr}")
                    all_success = False
            
            # Verificar estado real despues de activar
            time.sleep(1)
            self.check_services_status()
            
            if all_success and self.services_active:
                self.show_success("✅ ¡Servicios activados correctamente!\nProteccion restaurada")
            else:
                self.show_error("❌ Error al activar servicios. Revisa la terminal para detalles.")
                
        except Exception as e:
            error_msg = f"❌ Error critico: {str(e)}"
            print(f"Error critico: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(error_msg)
        finally:
            self.usb_btn.configure(state="normal")
            self.check_services_status()
    
    def update_proxy_settings_with_credentials(self):
        """Actualizar la configuracion de proxy con las credenciales actuales"""
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if username and password:
            for key in ['http_proxy', 'https_proxy', 'ftp_proxy', 'apt_proxy']:
                if key in self.proxy_settings:
                    current_url = self.proxy_settings[key]
                    if '://' in current_url:
                        protocol = current_url.split('://')[0]
                        rest = current_url.split('://')[1]
                        if '@' in rest:
                            host_port = rest.split('@')[1]
                            self.proxy_settings[key] = f"{protocol}://{username}:{password}@{host_port}"
                        else:
                            self.proxy_settings[key] = f"{protocol}://{username}:{password}@{rest}"
            
            self.save_config(self.proxy_settings)
    
    def _perform_disable_proxy(self, password):
        """Realizar la desactivacion de proxy"""
        print("=== DESACTIVANDO PROXY ===")
        
        try:
            # 1. Desactivar proxy del sistema (GNOME)
            print("1. Desactivando proxy del sistema...")
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'none'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al desactivar proxy del sistema: {result.stderr}")
                return False
            
            print("✓ Proxy del sistema desactivado")
            
            # 2. Limpiar variables de entorno del sistema (solo para esta sesion)
            print("2. Limpiando variables de entorno...")
            env_commands = [
                'unset http_proxy',
                'unset https_proxy', 
                'unset ftp_proxy',
                'unset no_proxy',
                'unset HTTP_PROXY',
                'unset HTTPS_PROXY',
                'unset FTP_PROXY',
                'unset NO_PROXY'
            ]
            
            for cmd in env_commands:
                try:
                    subprocess.run(cmd, shell=True, executable='/bin/bash', timeout=5)
                except Exception as e:
                    print(f"Advertencia al limpiar {cmd.split()[1]}: {e}")
            
            print("✓ Variables de entorno limpiadas")
            
            # 3. Limpiar proxy de apt
            print("3. Limpiando proxy de APT...")
            apt_proxy_file = "/etc/apt/apt.conf.d/99proxy"
            if Path(apt_proxy_file).exists():
                print(f"Eliminando archivo de configuracion de APT: {apt_proxy_file}")
                success, stdout, stderr = self.run_command_with_sudo(f"rm -f {apt_proxy_file}", password)
                if success:
                    print("✓ Proxy de APT limpiado")
                else:
                    print(f"Advertencia: No se pudo eliminar {apt_proxy_file}: {stderr}")
            else:
                print("✓ No existe archivo de proxy de APT")
            
            # 4. Limpiar /etc/environment
            print("4. Limpiando /etc/environment...")
            success, stdout, stderr = self.run_command_with_sudo(
                "sudo sed -i '/proxy/d;/PROXY/d' /etc/environment", 
                password
            )
            if success:
                print("✓ /etc/environment limpiado")
            else:
                print(f"Advertencia: No se pudo limpiar /etc/environment: {stderr}")
            
            print("=== PROXY DESACTIVADO CORRECTAMENTE ===")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Error: Tiempo de espera agotado durante la operacion")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en subprocess: {e}")
            return False
        except Exception as e:
            print(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _perform_enable_proxy(self, password):
        """Realizar la activacion de proxy"""
        print("=== ACTIVANDO PROXY ===")
        
        try:
            # 1. Configurar proxy del sistema (GNOME)
            print("1. Configurando proxy del sistema...")
            proxy_url = self.proxy_settings["http_proxy"]
            
            if '@' in proxy_url:
                proxy_host_port = proxy_url.split('@')[-1]
            else:
                proxy_host_port = proxy_url.split('://')[-1]
            
            if ':' in proxy_host_port:
                proxy_host = proxy_host_port.split(':')[0]
                proxy_port = proxy_host_port.split(':')[1].split('/')[0]
            else:
                proxy_host = proxy_host_port
                proxy_port = "3128"
            
            print(f"Host: {proxy_host}, Puerto: {proxy_port}")
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'manual'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al configurar modo manual: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'host', proxy_host
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al configurar host HTTP: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'port', proxy_port
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al configurar puerto HTTP: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'enabled', 'true'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al habilitar proxy HTTP: {result.stderr}")
                return False
            
            print("✓ Proxy del sistema configurado")
            
            # Configurar no_proxy
            print("2. Configurando no_proxy...")
            no_proxy_list = [item.strip() for item in self.proxy_settings["no_proxy"].split(',') if item.strip()]
            no_proxy_str = str(no_proxy_list).replace("'", '"')
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'ignore-hosts', no_proxy_str
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error al configurar no_proxy: {result.stderr}")
                return False
            
            print("✓ No_proxy configurado")
            
            # 2. Establecer variables de entorno en /etc/environment
            print("3. Configurando variables de entorno...")
            env_content = f"""
# Proxy Settings - Actualizado por Proxy Manager
http_proxy="{self.proxy_settings['http_proxy']}"
https_proxy="{self.proxy_settings['https_proxy']}"
ftp_proxy="{self.proxy_settings['ftp_proxy']}"
no_proxy="{self.proxy_settings['no_proxy']}"
HTTP_PROXY="{self.proxy_settings['http_proxy']}"
HTTPS_PROXY="{self.proxy_settings['https_proxy']}"
FTP_PROXY="{self.proxy_settings['ftp_proxy']}"
NO_PROXY="{self.proxy_settings['no_proxy']}"
"""
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_file:
                temp_file.write(env_content)
                temp_file_path = temp_file.name
            
            print(f"Archivo temporal creado: {temp_file_path}")
            
            success, stdout, stderr = self.run_command_with_sudo(
                f"cat {temp_file_path} >> /etc/environment && rm {temp_file_path}", 
                password
            )
            
            if success:
                print("✓ Variables de entorno actualizadas")
            else:
                print(f"Advertencia: No se pudo actualizar /etc/environment: {stderr}")
            
            # 3. Configurar proxy para apt
            print("4. Configurando proxy para APT...")
            apt_config = f"""
# Proxy Settings - Actualizado por Proxy Manager
Acquire::http::proxy "{self.proxy_settings['apt_proxy']}/";
Acquire::https::proxy "{self.proxy_settings['apt_proxy']}/";
Acquire::ftp::proxy "{self.proxy_settings['apt_proxy']}/";
"""
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.apt') as temp_file:
                temp_file.write(apt_config)
                temp_file_path = temp_file.name
            
            success, stdout, stderr = self.run_command_with_sudo(
                f"mv {temp_file_path} /etc/apt/apt.conf.d/99proxy && chmod 644 /etc/apt/apt.conf.d/99proxy", 
                password
            )
            
            if success:
                print("✓ Proxy para APT configurado")
            else:
                print(f"Advertencia: No se pudo configurar proxy para APT: {stderr}")
            
            print("=== PROXY ACTIVADO CORRECTAMENTE ===")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Error: Tiempo de espera agotado durante la operacion")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en subprocess: {e}")
            return False
        except Exception as e:
            print(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def open_config_window(self):
        """Abrir ventana de configuracion"""
        try:
            config_window = ctk.CTkToplevel(self.root)
            config_window.title("Configuracion de Proxy")
            config_window.geometry("550x500")
            
            # Centrar el dialogo
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 550) // 2
            y = (screen_height - 500) // 2
            config_window.geometry(f"+{x}+{y}")
            
            config_window.update_idletasks()
            time.sleep(0.1)
            
            config_window.transient(self.root)
            config_window.grab_set()
            config_window.focus_force()
            
            main_frame = ctk.CTkFrame(config_window)
            main_frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(main_frame, text="CONFIGURACION DE PROXY", 
                        font=("Arial", 18, "bold")).pack(pady=10)
            
            # Crear campos de entrada
            fields = [
                ("HTTP Proxy:", "http_proxy"),
                ("HTTPS Proxy:", "https_proxy"),
                ("FTP Proxy:", "ftp_proxy"),
                ("No Proxy:", "no_proxy"),
                ("APT Proxy:", "apt_proxy")
            ]
            
            entries = {}
            
            for label_text, key in fields:
                frame = ctk.CTkFrame(main_frame)
                frame.pack(fill="x", pady=5)
                
                ctk.CTkLabel(frame, text=label_text, width=100).pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame, width=400)
                entry.insert(0, self.proxy_settings.get(key, ""))
                entry.pack(side="left", padx=5)
                entries[key] = entry
            
            def save_config():
                for key, entry in entries.items():
                    self.proxy_settings[key] = entry.get()
                self.save_config(self.proxy_settings)
                self.show_success("✅ Configuracion guardada")
                config_window.destroy()
            
            def test_connection():
                proxy = entries["http_proxy"].get()
                try:
                    print(f"Probando conexion con proxy: {proxy}")
                    result = subprocess.run([
                        'curl', '-x', proxy, 'http://www.google.com', '--max-time', '10', '-I'
                    ], capture_output=True, text=True, timeout=15)
                    
                    print(f"Resultado curl: {result.stdout}")
                    print(f"Error: {result.stderr}")
                    print(f"Codigo de retorno: {result.returncode}")
                    
                    if result.returncode == 0 and "200 OK" in result.stdout:
                        self.show_success("✅ Conexion exitosa")
                    else:
                        error_msg = "❌ Error en la conexion"
                        if result.stderr:
                            error_msg += f"\nDetalles: {result.stderr[:100]}"
                        self.show_error(error_msg)
                except Exception as e:
                    self.show_error(f"❌ Error: {str(e)}")
            
            btn_frame = ctk.CTkFrame(main_frame)
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="💾 Guardar", command=save_config,
                         fg_color="#2ecc71", width=120).pack(side="left", padx=10)
            
            ctk.CTkButton(btn_frame, text="🔍 Probar Conexion", command=test_connection,
                         fg_color="#3498db", width=120).pack(side="left", padx=10)
            
            ctk.CTkButton(btn_frame, text="❌ Cancelar", command=config_window.destroy,
                         fg_color="#e74c3c", width=120).pack(side="left", padx=10)
            
        except Exception as e:
            print(f"Error abriendo ventana de configuracion: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"❌ Error al abrir configuracion: {str(e)}")
    
    def show_success(self, message):
        """Mostrar mensaje de exito con manejo de errores mejorado"""
        try:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Exito")
            dialog.geometry("300x150")
            
            # Centrar el dialogo
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 150) // 2
            dialog.geometry(f"+{x}+{y}")
            
            dialog.update_idletasks()
            time.sleep(0.1)
            
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.focus_force()
            
            frame = ctk.CTkFrame(dialog)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(frame, text=message, font=("Arial", 14, "bold"),
                        text_color="#2ecc71").pack(pady=20)
            
            ctk.CTkButton(frame, text="OK", command=dialog.destroy,
                         fg_color="#2ecc71", width=100).pack(pady=10)
        except Exception as e:
            print(f"Error mostrando mensaje de exito: {e}")
            print(f"✅ {message}")
    
    def show_error(self, message):
        """Mostrar mensaje de error con manejo de errores mejorado"""
        try:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Error")
            dialog.geometry("400x200")
            
            # Centrar el dialogo
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 200) // 2
            dialog.geometry(f"+{x}+{y}")
            
            dialog.update_idletasks()
            time.sleep(0.1)
            
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.focus_force()
            
            frame = ctk.CTkFrame(dialog)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(frame, text=message, font=("Arial", 12),
                        text_color="#e74c3c", wraplength=350).pack(pady=20)
            
            ctk.CTkButton(frame, text="OK", command=dialog.destroy,
                         fg_color="#e74c3c", width=100).pack(pady=10)
        except Exception as e:
            print(f"Error mostrando mensaje de error: {e}")
            print(f"❌ {message}")
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_exc()
    
    def run(self):
        """Ejecutar la aplicacion"""
        print("=== INICIANDO PROXY MANAGER ===")
        print(f"Python version: {sys.version}")
        print(f"CustomTkinter version: {ctk.__version__ if hasattr(ctk, '__version__') else 'desconocida'}")
        
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error fatal en mainloop: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Verificar si customtkinter esta instalado
    try:
        import customtkinter
    except ImportError as e:
        print("❌ Error: customtkinter no esta instalado")
        print("Instala con: pip install customtkinter")
        print("O con sudo: sudo pip install customtkinter")
        print(f"Detalles del error: {e}")
        exit(1)
    
    print("✅ CustomTkinter importado correctamente")
    app = ProxyManagerApp()
    app.run()