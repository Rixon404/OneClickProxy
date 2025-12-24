"""
Main window UI for Proxy Manager
"""
import customtkinter as ctk
import time


class MainWindow:
    """Main application window UI"""
    
    def __init__(self, controller):
        self.controller = controller
        
        # Configure customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Proxy Manager - Ubuntu")
        self.root.geometry("1500x1000")
        self.root.resizable(True, True)
        
        # Create UI elements
        self.create_widgets()
        
        # Initial status checks
        self.controller.check_proxy_status()
        self.controller.check_services_status()
    
    def create_widgets(self):
        """Create the user interface"""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="GESTOR DE PROXY Y USB", 
            font=("Arial", 24, "bold"),
            text_color="#3498db"
        )
        title_label.pack(pady=(10, 5))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame, 
            text="Control total con un clic",
            font=("Arial", 14)
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Credentials frame
        credentials_frame = ctk.CTkFrame(main_frame)
        credentials_frame.pack(padx=20, pady=10, fill="x")
        
        # User label and field
        user_frame = ctk.CTkFrame(credentials_frame)
        user_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(user_frame, text="Usuario:", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        self.user_entry = ctk.CTkEntry(user_frame, width=400)
        self.user_entry.insert(0, self.controller.get_username())
        self.user_entry.pack(side="left", padx=5)
        
        # Password label and field
        pass_frame = ctk.CTkFrame(credentials_frame)
        pass_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(pass_frame, text="Contraseña:", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        self.pass_entry = ctk.CTkEntry(pass_frame, show="*", width=400)
        self.pass_entry.insert(0, self.controller.get_password())
        self.pass_entry.pack(side="left", padx=5)
        
        # Show/hide password button
        self.show_pass_var = ctk.BooleanVar()
        self.show_pass_btn = ctk.CTkCheckBox(pass_frame, text="Mostrar", variable=self.show_pass_var, 
                                            command=self.toggle_password_visibility)
        self.show_pass_btn.pack(side="right", padx=(5, 10))
        
        # Credentials buttons frame (horizontal)
        creds_btn_frame = ctk.CTkFrame(credentials_frame)
        creds_btn_frame.pack(pady=10, fill="x")
        
        # Save credentials button - blue color #3498db
        save_creds_btn = ctk.CTkButton(creds_btn_frame, text="💾 Guardar Credenciales", 
                                      command=self.save_current_credentials,
                                      fg_color="#3498db",  # Same blue as title
                                      text_color="white",  # White text
                                      hover_color="#2980b9",  # Darker blue for hover
                                      height=30)
        save_creds_btn.pack(side="left", padx=(20, 10), pady=5)
        
        # Update password in all proxies button - blue color #3498db
        update_pass_btn = ctk.CTkButton(creds_btn_frame, text="🔄 Actualizar Contraseña", 
                                       command=self.update_all_proxies_password,
                                       fg_color="#3498db",  # Same blue as title
                                       text_color="white",  # White text
                                       hover_color="#2980b9",  # Darker blue for hover
                                       height=30)
        update_pass_btn.pack(side="left", padx=(10, 20), pady=5)
        
        # Proxy button frame
        proxy_button_frame = ctk.CTkFrame(main_frame)
        proxy_button_frame.pack(padx=20, pady=10, fill="x")
        
        # Single dynamic proxy button
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
        
        # Current proxy status
        self.proxy_status_label = ctk.CTkLabel(
            main_frame,
            text="Estado Proxy: ❌ DESACTIVADO", 
            font=("Arial", 14, "bold"),
            text_color="#e74c3c"
        )
        self.proxy_status_label.pack(pady=5)
        
        # USB services control section
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
        
        # Dynamic services button - BIGGER!
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
        
        # Current services status
        self.usb_status_label = ctk.CTkLabel(
            usb_frame,
            text="Estado Servicios: ✅ ACTIVOS", 
            font=("Arial", 12, "bold"),
            text_color="#2ecc71"
        )
        self.usb_status_label.pack(pady=(0, 15))
        
        # Configuration button
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
        
        # Sudo permissions indicator
        self.sudo_label = ctk.CTkLabel(
            main_frame,
            text="🔒 Se necesitarán permisos de administrador para ambas operaciones",
            font=("Arial", 10),
            text_color="#f39c12"
        )
        self.sudo_label.pack(pady=(5, 15))
    
    def toggle_password_visibility(self):
        """Show or hide password"""
        if self.show_pass_var.get():
            self.pass_entry.configure(show="")
        else:
            self.pass_entry.configure(show="*")
    
    def save_current_credentials(self):
        """Save current credentials"""
        username = self.user_entry.get()
        password = self.pass_entry.get()
        self.controller.save_credentials(username, password)
        self.show_success("✅ Credenciales guardadas correctamente")
    
    def update_all_proxies_password(self):
        """Update password in all system proxies without restart"""
        self.controller.update_all_proxies_password(self.user_entry.get(), self.pass_entry.get())
    
    def toggle_proxy(self):
        """Toggle between enable and disable proxy"""
        self.controller.toggle_proxy()
    
    def toggle_usb_services(self):
        """Toggle between stop and start USB services"""
        self.controller.toggle_usb_services()
    
    def open_config_window(self):
        """Open configuration window"""
        self.controller.open_config_window()
    
    def update_proxy_status_display(self, is_active):
        """Update the displayed proxy status"""
        if is_active:
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
    
    def update_services_status_display(self, is_active):
        """Update the displayed services status"""
        if is_active:
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
    
    def show_success(self, message):
        """Show success message"""
        try:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Éxito")
            dialog.geometry("500x300")
            
            # Center the dialog
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
            print(f"Error showing success message: {e}")
            print(f"✅ {message}")
    
    def show_error(self, message):
        """Show error message"""
        try:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Error")
            dialog.geometry("600x350")
            
            # Center the dialog
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
            print(f"Error showing error message: {e}")
            print(f"❌ {message}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()