"""
Main controller for Proxy Manager
"""
import customtkinter as ctk
import time
from pathlib import Path
import tempfile
import subprocess


class MainController:
    """Main application controller"""
    
    def __init__(self, config_manager, proxy_model, view):
        self.config = config_manager
        self.model = proxy_model
        self.view = view
        
        # Admin password cache
        self.admin_password_cache = None
    
    def check_proxy_status(self):
        """Check current proxy status and update UI"""
        is_active = self.model.check_proxy_status()
        self.view.update_proxy_status_display(is_active)
    
    def check_services_status(self):
        """Check current services status and update UI"""
        is_active = self.model.check_services_status()
        self.view.update_services_status_display(is_active)
    
    def get_username(self):
        """Get current username from config"""
        return self.config.credentials.get("username", "")
    
    def get_password(self):
        """Get current password from config"""
        return self.config.credentials.get("password", "")
    
    def save_credentials(self, username, password):
        """Save credentials to config"""
        self.config.credentials["username"] = username
        self.config.credentials["password"] = password
        self.config.save_credentials()
    
    def update_all_proxies_password(self, username, password):
        """Update password in all system proxies without restart"""
        try:
            self.view.usb_status_label.configure(text="Estado: ⏳ Actualizando contraseñas...", text_color="#f39c12")
            self.view.root.update_idletasks()
            time.sleep(0.1)
            
            # Use cached password or ask for it
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password  # Cache it
            
            if not password:
                self.view.show_error("❌ Operación cancelada por el usuario")
                return
            
            if not username or not password:
                self.view.show_error("❌ Usuario y contraseña no pueden estar vacíos")
                return
            
            # Update proxy settings with new credentials
            self.model.update_proxy_settings_with_credentials(username, password)
            
            # Update /etc/environment
            env_content = f"""
# Proxy Settings - Actualizado por Proxy Manager
\thttp_proxy="{self.config.proxy_settings['http_proxy']}"
\thttps_proxy="{self.config.proxy_settings['https_proxy']}"
\tftp_proxy="{self.config.proxy_settings['ftp_proxy']}"
\tno_proxy="{self.config.proxy_settings['no_proxy']}"
\tHTTP_PROXY="{self.config.proxy_settings['http_proxy']}"
\tHTTPS_PROXY="{self.config.proxy_settings['https_proxy']}"
\tFTP_PROXY="{self.config.proxy_settings['ftp_proxy']}"
\tNO_PROXY="{self.config.proxy_settings['no_proxy']}"
"""
            # Write to temporary file and move with sudo (avoids redirection issues)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as tmp_env_file:
                tmp_env_file.write(env_content)
                tmp_env_path = tmp_env_file.name

            success_env, stdout_env, stderr_env = self.model.run_command_with_sudo(
                f"mv {tmp_env_path} /etc/environment && chmod 644 /etc/environment",
                password
            )
            
            # Update proxy for apt
            apt_config = f"""
# Proxy Settings - Actualizado por Proxy Manager
Acquire::http::proxy "{self.config.proxy_settings['apt_proxy']}/";
Acquire::https::proxy "{self.config.proxy_settings['apt_proxy']}/";
Acquire::ftp::proxy "{self.config.proxy_settings['apt_proxy']}/";
"""
            # Write to temporary file and move with sudo
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.apt') as tmp_apt_file:
                tmp_apt_file.write(apt_config)
                tmp_apt_path = tmp_apt_file.name

            success_apt, stdout_apt, stderr_apt = self.model.run_command_with_sudo(
                f"mv {tmp_apt_path} /etc/apt/apt.conf.d/99proxy && chmod 644 /etc/apt/apt.conf.d/99proxy",
                password
            )
            
            if success_env and success_apt:
                # Show updated environment variables in current session
                env_commands = [
                    f'export http_proxy="{self.config.proxy_settings["http_proxy"]}"',
                    f'export https_proxy="{self.config.proxy_settings["https_proxy"]}"',
                    f'export ftp_proxy="{self.config.proxy_settings["ftp_proxy"]}"',
                    f'export no_proxy="{self.config.proxy_settings["no_proxy"]}"',
                    f'export HTTP_PROXY="{self.config.proxy_settings["http_proxy"]}"',
                    f'export HTTPS_PROXY="{self.config.proxy_settings["https_proxy"]}"',
                    f'export FTP_PROXY="{self.config.proxy_settings["ftp_proxy"]}"',
                    f'export NO_PROXY="{self.config.proxy_settings["no_proxy"]}"'
                ]
                
                for cmd in env_commands:
                    try:
                        subprocess.run(cmd, shell=True, executable='/bin/bash', timeout=5)
                    except Exception as e:
                        print(f"Warning updating environment variable: {e}")
                
                self.view.show_success(f"✅ ¡Contraseñas actualizadas correctamente en {len(['http_proxy', 'https_proxy', 'ftp_proxy', 'apt_proxy'])} proxies!\nNo es necesario reiniciar el proxy")
            else:
                error_msg = "❌ Error al actualizar archivos de configuración"
                if not success_env:
                    error_msg += f"\n/etc/environment: {stderr_env}"
                if not success_apt:
                    error_msg += f"\nAPT config: {stderr_apt}"
                self.view.show_error(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Error crítico: {str(e)}"
            print(f"Critical error: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(error_msg)
        finally:
            # Restore original status after operation
            self.check_services_status()
    
    def toggle_proxy(self):
        """Toggle proxy between active/inactive"""
        if self.model.proxy_active:
            self.disable_proxy()
        else:
            self.enable_proxy()
    
    def enable_proxy(self):
        """Enable proxy"""
        try:
            self.view.proxy_status_label.configure(text="Estado Proxy: ⏳ Activando...", text_color="#f39c12")
            self.view.proxy_btn.configure(state="disabled")
            self.view.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.view.show_error("❌ Operación cancelada por el usuario")
                self.check_proxy_status()
                return
            
            # Update proxy settings with current credentials
            self.model.update_proxy_settings_with_credentials(
                self.view.user_entry.get(), 
                self.view.pass_entry.get()
            )
            
            success = self.model._perform_enable_proxy(password)
            
            if success:
                self.model.proxy_active = True
                self.check_proxy_status()
                self.view.show_success("✅ ¡Proxy activado correctamente!")
            else:
                self.view.show_error("❌ Error al activar el proxy. Revisa la terminal para más detalles.")
                self.check_proxy_status()
                
        except Exception as e:
            error_msg = f"❌ Error crítico: {str(e)}"
            print(f"Critical error: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(error_msg)
            self.check_proxy_status()
        finally:
            self.view.proxy_btn.configure(state="normal")
    
    def disable_proxy(self):
        """Disable proxy"""
        try:
            self.view.proxy_status_label.configure(text="Estado Proxy: ⏳ Desactivando...", text_color="#f39c12")
            self.view.proxy_btn.configure(state="disabled")
            self.view.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.view.show_error("❌ Operación cancelada por el usuario")
                self.check_proxy_status()
                return
            
            success = self.model._perform_disable_proxy(password)
            
            if success:
                self.model.proxy_active = False
                self.check_proxy_status()
                self.view.show_success("✅ ¡Proxy desactivado correctamente!")
            else:
                self.view.show_error("❌ Error al desactivar el proxy. Revisa la terminal para más detalles.")
                self.check_proxy_status()
                
        except Exception as e:
            error_msg = f"❌ Error crítico: {str(e)}"
            print(f"Critical error: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(error_msg)
            self.check_proxy_status()
        finally:
            self.view.proxy_btn.configure(state="normal")
    
    def toggle_usb_services(self):
        """Toggle USB services between active/inactive"""
        if self.model.services_active:
            self.stop_usb_services()
        else:
            self.start_usb_services()
    
    def stop_usb_services(self):
        """Stop USB services"""
        try:
            self.view.usb_status_label.configure(text="Estado Servicios: ⏳ Deteniendo...", text_color="#f39c12")
            self.view.usb_btn.configure(state="disabled")
            self.view.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.view.show_error("❌ Operación cancelada por el usuario")
                self.check_services_status()
                return
            
            success = self.model.stop_usb_services(password)
            
            if success:
                self.check_services_status()
                self.view.show_success("✅ ¡Servicios detenidos correctamente!\nAhora puedes conectar memorias USB")
            else:
                self.view.show_error("❌ Error al detener servicios. Revisa la terminal para detalles.")
                self.check_services_status()
                
        except Exception as e:
            error_msg = f"❌ Error crítico: {str(e)}"
            print(f"Critical error: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(error_msg)
        finally:
            self.view.usb_btn.configure(state="normal")
            self.check_services_status()
    
    def start_usb_services(self):
        """Start USB services"""
        try:
            self.view.usb_status_label.configure(text="Estado Servicios: ⏳ Activando...", text_color="#f39c12")
            self.view.usb_btn.configure(state="disabled")
            self.view.root.update_idletasks()
            time.sleep(0.1)
            
            password = self.admin_password_cache
            if not password:
                password = self.ask_sudo_password()
                if password:
                    self.admin_password_cache = password
            
            if not password:
                self.view.show_error("❌ Operación cancelada por el usuario")
                self.check_services_status()
                return
            
            success = self.model.start_usb_services(password)
            
            if success:
                self.check_services_status()
                self.view.show_success("✅ ¡Servicios activados correctamente!\nProtección restaurada")
            else:
                self.view.show_error("❌ Error al activar servicios. Revisa la terminal para detalles.")
                self.check_services_status()
                
        except Exception as e:
            error_msg = f"❌ Error crítico: {str(e)}"
            print(f"Critical error: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(error_msg)
        finally:
            self.view.usb_btn.configure(state="normal")
            self.check_services_status()
    
    def ask_sudo_password(self):
        """Securely ask for admin password"""
        try:
            # If we already have a password in cache, use it
            if self.admin_password_cache:
                return self.admin_password_cache
            
            dialog = ctk.CTkToplevel(self.view.root)
            dialog.title("Contraseña de administrador")
            dialog.geometry("500x300")
            
            # Center the dialog
            screen_width = self.view.root.winfo_screenwidth()
            screen_height = self.view.root.winfo_screenheight()
            x = (screen_width - 350) // 2
            y = (screen_height - 180) // 2
            dialog.geometry(f"+{x}+{y}")
            
            dialog.update_idletasks()
            time.sleep(0.1)
            
            dialog.transient(self.view.root)
            dialog.grab_set()
            dialog.focus_force()
            
            frame = ctk.CTkFrame(dialog)
            frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(frame, text="Introduce tu contraseña de administrador:", 
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
            
            self.view.root.wait_window(dialog)
            
            # Cache the password if a valid one is provided
            if result[0]:
                self.admin_password_cache = result[0]
            
            return result[0]
            
        except Exception as e:
            print(f"Error creating password dialog: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def open_config_window(self):
        """Open configuration window"""
        try:
            config_window = ctk.CTkToplevel(self.view.root)
            config_window.title("Configuración de Proxy")
            config_window.geometry("600x550")
            
            # Center the dialog
            screen_width = self.view.root.winfo_screenwidth()
            screen_height = self.view.root.winfo_screenheight()
            x = (screen_width - 550) // 2
            y = (screen_height - 500) // 2
            config_window.geometry(f"+{x}+{y}")
            
            config_window.update_idletasks()
            time.sleep(0.1)
            
            config_window.transient(self.view.root)
            config_window.grab_set()
            config_window.focus_force()
            
            main_frame = ctk.CTkFrame(config_window)
            main_frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            ctk.CTkLabel(main_frame, text="CONFIGURACIÓN DE PROXY", 
                        font=("Arial", 18, "bold")).pack(pady=10)
            
            # Create entry fields
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
                entry.insert(0, self.config.proxy_settings.get(key, ""))
                entry.pack(side="left", padx=5)
                entries[key] = entry
            
            def save_config():
                for key, entry in entries.items():
                    self.config.proxy_settings[key] = entry.get()
                self.config.save_config(self.config.proxy_settings)
                self.view.show_success("✅ Configuración guardada")
                config_window.destroy()
            
            def test_connection():
                proxy = entries["http_proxy"].get()
                try:
                    print(f"Testing connection with proxy: {proxy}")
                    result = subprocess.run([
                        'curl', '-x', proxy, 'http://www.google.com', '--max-time', '10', '-I'
                    ], capture_output=True, text=True, timeout=15)
                    
                    print(f"curl result: {result.stdout}")
                    print(f"Error: {result.stderr}")
                    print(f"Return code: {result.returncode}")
                    
                    if result.returncode == 0 and "200 OK" in result.stdout:
                        self.view.show_success("✅ Conexión exitosa")
                    else:
                        error_msg = "❌ Error en la conexión"
                        if result.stderr:
                            error_msg += f"\nDetalles: {result.stderr[:100]}"
                        self.view.show_error(error_msg)
                except Exception as e:
                    self.view.show_error(f"❌ Error: {str(e)}")
            
            btn_frame = ctk.CTkFrame(main_frame)
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="💾 Guardar", command=save_config,
                         fg_color="#2ecc71", width=120).pack(side="left", padx=10)
            
            ctk.CTkButton(btn_frame, text="🔍 Probar Conexion", command=test_connection,
                         fg_color="#3498db", width=120).pack(side="left", padx=10)
            
            ctk.CTkButton(btn_frame, text="❌ Cancelar", command=config_window.destroy,
                         fg_color="#e74c3c", width=120).pack(side="left", padx=10)
            
        except Exception as e:
            print(f"Error opening config window: {e}")
            import traceback
            traceback.print_exc()
            self.view.show_error(f"❌ Error al abrir configuración: {str(e)}")