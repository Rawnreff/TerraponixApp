#!/usr/bin/env python3
"""
Terraponix Backend Server Launcher

Simple script to run the Flask backend server with proper configuration.
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def get_local_ip():
    """Get local IP address for network configuration"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    """Main function to run the server"""
    print("🌱 Terraponix Backend Server")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Get local IP
    local_ip = get_local_ip()
    
    print("\n🚀 Starting Terraponix Backend Server...")
    print(f"📡 Server will be available at:")
    print(f"   Local:    http://127.0.0.1:5000")
    print(f"   Network:  http://{local_ip}:5000")
    print(f"   Health:   http://{local_ip}:5000/api/health")
    print("\n📱 Configure your mobile app to use:")
    print(f"   API URL:  http://{local_ip}:5000/api")
    print("\n🔌 ESP32 should send data to:")
    print(f"   Endpoint: http://{local_ip}:5000/api/sensor-data")
    print("\n" + "=" * 50)
    print("📊 Dashboard endpoints:")
    print(f"   Current Data:    GET  /api/current-data")
    print(f"   Historical Data: GET  /api/historical-data")
    print(f"   Controls:        GET  /api/controls")
    print(f"   Alerts:          GET  /api/alerts")
    print(f"   Send Command:    POST /api/device-command")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError:
        print("❌ Could not import Flask app. Make sure app.py exists.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()