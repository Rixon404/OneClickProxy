# Proxy Manager

A GUI application to manage proxy settings and USB services on Ubuntu systems. This application allows users to easily enable/disable proxy settings and control USB services (such as Kaspersky antivirus) that may block USB device access.

## Features

- **Proxy Management**: Enable/disable system-wide proxy settings for HTTP, HTTPS, FTP, and APT
- **USB Service Control**: Start/stop Kaspersky services to allow USB device access
- **Credential Management**: Securely store and update proxy credentials
- **Configuration**: Edit proxy settings through a dedicated configuration window
- **Connection Testing**: Test proxy connection directly from the application

## Requirements

- Python 3.8 or higher
- Ubuntu/Linux system with GNOME desktop environment
- Administrative privileges (sudo access)

## Installation

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install customtkinter
   ```
3. Run the application:
   ```bash
   python -m proxy_manager
   ```

## Usage

1. Enter your proxy credentials in the username and password fields
2. Use the "Guardar Credenciales" button to save your credentials
3. Use "Actualizar Contraseña" to update the password in all proxy configurations
4. Click "ACTIVAR PROXY" to enable proxy settings system-wide
5. Use the USB services controls to stop/start services as needed

## Architecture

The application follows the Model-View-Controller (MVC) pattern:

- **Models**: Handle system operations and proxy management
- **Views**: Provide the GUI interface using CustomTkinter
- **Controllers**: Coordinate between models and views
- **Config**: Manage application settings and user credentials

## License

This project is licensed under the MIT License - see the LICENSE file for details.