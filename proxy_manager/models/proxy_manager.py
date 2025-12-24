"""
Proxy management model for Proxy Manager
"""
import subprocess
import tempfile
from pathlib import Path


class ProxyModel:
    """Handles proxy operations and system configuration"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.proxy_active = False
        self.services_active = True
    
    def check_proxy_status(self):
        """Check current proxy status"""
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.system.proxy', 'mode'], 
                                  capture_output=True, text=True, timeout=5)
            mode = result.stdout.strip().strip("'")
            self.proxy_active = (mode == 'manual')
            return self.proxy_active
        except Exception as e:
            print(f"Error checking proxy status: {e}")
            return False
    
    def check_services_status(self):
        """Check status of Kaspersky services"""
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
                    print(f"Timeout checking service {service}")
                    all_active = False
                    break
            
            self.services_active = all_active
            return all_active
        except Exception as e:
            print(f"Error checking services: {e}")
            self.services_active = True
            return True
    
    def _perform_enable_proxy(self, password):
        """Perform proxy activation"""
        print("=== ACTIVATING PROXY ===")
        
        try:
            # 1. Configure system proxy (GNOME)
            print("1. Configuring system proxy...")
            proxy_url = self.config.proxy_settings["http_proxy"]
            
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
            
            print(f"Host: {proxy_host}, Port: {proxy_port}")
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'manual'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error setting manual mode: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'host', proxy_host
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error setting HTTP host: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'port', proxy_port
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error setting HTTP port: {result.stderr}")
                return False
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy.http', 'enabled', 'true'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error enabling HTTP proxy: {result.stderr}")
                return False
            
            print("✓ System proxy configured")
            
            # Configure no_proxy
            print("2. Configuring no_proxy...")
            no_proxy_list = [item.strip() for item in self.config.proxy_settings["no_proxy"].split(',') if item.strip()]
            no_proxy_str = str(no_proxy_list).replace("'", '"')
            
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'ignore-hosts', no_proxy_str
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error configuring no_proxy: {result.stderr}")
                return False
            
            print("✓ No_proxy configured")
            
            # 2. Set environment variables in /etc/environment
            print("3. Configuring environment variables...")
            env_content = f"""
# Proxy Settings - Updated by Proxy Manager
\thttp_proxy="{self.config.proxy_settings['http_proxy']}"
\thttps_proxy="{self.config.proxy_settings['https_proxy']}"
\tftp_proxy="{self.config.proxy_settings['ftp_proxy']}"
\tno_proxy="{self.config.proxy_settings['no_proxy']}"
\tHTTP_PROXY="{self.config.proxy_settings['http_proxy']}"
\tHTTPS_PROXY="{self.config.proxy_settings['https_proxy']}"
\tFTP_PROXY="{self.config.proxy_settings['ftp_proxy']}"
\tNO_PROXY="{self.config.proxy_settings['no_proxy']}"
"""
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_file:
                temp_file.write(env_content)
                temp_file_path = temp_file.name
            
            print(f"Temporary file created: {temp_file_path}")
            
            # Move the temporary file to avoid redirection issues
            success, stdout, stderr = self.run_command_with_sudo(
                f"mv {temp_file_path} /etc/environment && chmod 644 /etc/environment",
                password
            )
            
            if success:
                print("✓ Environment variables updated")
            else:
                print(f"Warning: Could not update /etc/environment: {stderr}")
            
            # 3. Configure proxy for apt
            print("4. Configuring proxy for APT...")
            apt_config = f"""
# Proxy Settings - Updated by Proxy Manager
Acquire::http::proxy "{self.config.proxy_settings['apt_proxy']}/";
Acquire::https::proxy "{self.config.proxy_settings['apt_proxy']}/";
Acquire::ftp::proxy "{self.config.proxy_settings['apt_proxy']}/";
"""
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.apt') as temp_file:
                temp_file.write(apt_config)
                temp_file_path = temp_file.name
            
            success, stdout, stderr = self.run_command_with_sudo(
                f"mv {temp_file_path} /etc/apt/apt.conf.d/99proxy && chmod 644 /etc/apt/apt.conf.d/99proxy",
                password
            )
            
            if success:
                print("✓ APT proxy configured")
            else:
                print(f"Warning: Could not configure APT proxy: {stderr}")
            
            print("=== PROXY ACTIVATED SUCCESSFULLY ===")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Error: Operation timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error in subprocess: {e}")
            return False
        except Exception as e:
            print(f"❌ General error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _perform_disable_proxy(self, password):
        """Perform proxy deactivation"""
        print("=== DEACTIVATING PROXY ===")
        
        try:
            # 1. Disable system proxy (GNOME)
            print("1. Disabling system proxy...")
            result = subprocess.run([
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', 'none'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Error disabling system proxy: {result.stderr}")
                return False
            
            print("✓ System proxy disabled")
            
            # 2. Clear system environment variables (for this session only)
            print("2. Clearing environment variables...")
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
                    print(f"Warning clearing {cmd.split()[1]}: {e}")
            
            print("✓ Environment variables cleared")
            
            # 3. Clear apt proxy
            print("3. Clearing APT proxy...")
            apt_proxy_file = "/etc/apt/apt.conf.d/99proxy"
            if Path(apt_proxy_file).exists():
                print(f"Removing APT config file: {apt_proxy_file}")
                success, stdout, stderr = self.run_command_with_sudo(f"rm -f {apt_proxy_file}", password)
                if success:
                    print("✓ APT proxy cleared")
                else:
                    print(f"Warning: Could not remove {apt_proxy_file}: {stderr}")
            else:
                print("✓ No APT proxy file exists")
            
            # 4. Clear /etc/environment
            print("4. Clearing /etc/environment...")
            success, stdout, stderr = self.run_command_with_sudo(
                "sed -i '/proxy/d;/PROXY/d' /etc/environment",
                password
            )
            if success:
                print("✓ /etc/environment cleared")
            else:
                print(f"Warning: Could not clear /etc/environment: {stderr}")
            
            print("=== PROXY DEACTIVATED SUCCESSFULLY ===")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Error: Operation timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error in subprocess: {e}")
            return False
        except Exception as e:
            print(f"❌ General error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_usb_services(self, password):
        """Stop Kaspersky services for USB access"""
        print("=== STOPPING SERVICES FOR USB ===")
        
        services = ["klnagent64.service", "klnagent64"]
        all_success = True
        
        for service in services:
            print(f"Stopping service: {service}")
            success, stdout, stderr = self.run_command_with_sudo(f"systemctl stop {service}", password)
            
            if success:
                print(f"✓ Service {service} stopped successfully")
            else:
                print(f"❌ Error stopping {service}: {stderr}")
                all_success = False
        
        # Verify actual status after stopping
        self.check_services_status()
        
        return all_success and not self.services_active
    
    def start_usb_services(self, password):
        """Start Kaspersky services for USB access"""
        print("=== STARTING SERVICES FOR USB ===")
        
        services = ["klnagent64", "klnagent64.service"]
        all_success = True
        
        for service in services:
            print(f"Starting service: {service}")
            success, stdout, stderr = self.run_command_with_sudo(f"systemctl start {service}", password)
            
            if success:
                print(f"✓ Service {service} started successfully")
            else:
                print(f"❌ Error starting {service}: {stderr}")
                all_success = False
        
        # Verify actual status after starting
        self.check_services_status()
        
        return all_success and self.services_active
    
    def run_command_with_sudo(self, command, password):
        """Execute command with sudo using password"""
        if not password:
            return False, "", "Empty password"
        try:
            full_cmd = f"sudo -S {command}"
            result = subprocess.run(
                full_cmd,
                shell=True,
                input=password + "\n",
                capture_output=True,
                text=True,
                timeout=30,
                executable='/bin/bash'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def update_proxy_settings_with_credentials(self, username, password):
        """Update proxy settings with current credentials"""
        if username and password:
            for key in ['http_proxy', 'https_proxy', 'ftp_proxy', 'apt_proxy']:
                if key in self.config.proxy_settings:
                    current_url = self.config.proxy_settings[key]
                    if '://' in current_url:
                        protocol = current_url.split('://')[0]
                        rest = current_url.split('://')[1]
                        if '@' in rest:
                            host_port = rest.split('@')[1]
                            self.config.proxy_settings[key] = f"{protocol}://{username}:{password}@{host_port}"
                        else:
                            self.config.proxy_settings[key] = f"{protocol}://{username}:{password}@{rest}"
            
            self.config.save_config(self.config.proxy_settings)