#!/usr/bin/env python3
"""
Terraponix Greenhouse System Startup Script
This script starts the complete greenhouse automation system
"""

import os
import sys
import subprocess
import time
import threading
import signal
from pathlib import Path

class GreenhouseSystemManager:
    def __init__(self):
        self.processes = []
        self.running = False
        
    def print_banner(self):
        """Print system banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🌱 TERRAPONIX GREENHOUSE SYSTEM 🌱                      ║
║                          Automated IoT Agriculture                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Features:                                                                   ║
║  • Real-time sensor monitoring (Temperature, Humidity, pH, Soil Moisture)   ║
║  • Automated irrigation and climate control                                  ║
║  • Remote monitoring via web dashboard                                       ║
║  • ESP32 integration with WiFi connectivity                                  ║
║  • Historical data logging and analysis                                      ║
║  • Manual and automatic control modes                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking system dependencies...")
        
        required_packages = [
            'flask',
            'flask-cors',
            'requests'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} - MISSING")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("📦 Installing missing packages...")
            
            for package in missing_packages:
                try:
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install', package
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"   ✅ Installed {package}")
                except subprocess.CalledProcessError:
                    print(f"   ❌ Failed to install {package}")
                    return False
        
        print("✅ All dependencies satisfied!")
        return True
    
    def check_files(self):
        """Check if required files exist"""
        print("\n📁 Checking system files...")
        
        required_files = [
            'greenhouse_api.py',
            'esp32/terraponix_greenhouse.ino'
        ]
        
        optional_files = [
            'test_greenhouse_system.py'
        ]
        
        all_good = True
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} - MISSING (REQUIRED)")
                all_good = False
        
        for file_path in optional_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path} (optional)")
            else:
                print(f"   ⚠️  {file_path} - MISSING (optional)")
        
        return all_good
    
    def get_network_info(self):
        """Get network information"""
        print("\n🌐 Network Information:")
        
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"   Hostname: {hostname}")
            print(f"   Local IP: {local_ip}")
            print(f"   Server URL: http://{local_ip}:5000")
            print(f"   Dashboard: http://{local_ip}:5000/dashboard")
            return local_ip
        except Exception as e:
            print(f"   ❌ Could not determine network info: {e}")
            return "localhost"
    
    def start_api_server(self):
        """Start the API server"""
        print("\n🚀 Starting Greenhouse API Server...")
        
        try:
            # Start the API server process
            process = subprocess.Popen([
                sys.executable, 'greenhouse_api.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.processes.append(('API Server', process))
            print("   ✅ API Server started successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to start API server: {e}")
            return False
    
    def wait_for_server(self, timeout=30):
        """Wait for server to be ready"""
        print("\n⏳ Waiting for server to be ready...")
        
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:5000/', timeout=2)
                if response.status_code == 200:
                    print("   ✅ Server is ready!")
                    return True
            except:
                pass
            
            print("   ⏳ Server starting...")
            time.sleep(2)
        
        print("   ❌ Server failed to start within timeout")
        return False
    
    def show_esp32_instructions(self):
        """Show ESP32 setup instructions"""
        print("\n📱 ESP32 Setup Instructions:")
        print("=" * 50)
        print("1. Install Arduino IDE and required libraries:")
        print("   • WiFi library (built-in)")
        print("   • HTTPClient library (built-in)")
        print("   • ArduinoJson library")
        print("   • DHT sensor library")
        print("   • ESP32Servo library")
        print("")
        print("2. Open esp32/terraponix_greenhouse.ino in Arduino IDE")
        print("")
        print("3. Update the following in the code:")
        print("   • WiFi SSID and password")
        print("   • Server IP address (your computer's IP)")
        print("")
        print("4. Select your ESP32 board and upload the code")
        print("")
        print("5. Open Serial Monitor to see device status")
        print("")
        print("6. Your ESP32 will automatically:")
        print("   • Connect to WiFi")
        print("   • Register with the server")
        print("   • Start sending sensor data")
        print("   • Create a local web interface")
    
    def show_usage_instructions(self, local_ip):
        """Show system usage instructions"""
        print("\n📖 System Usage:")
        print("=" * 50)
        print(f"🌐 Web Dashboard: http://{local_ip}:5000/dashboard")
        print(f"📊 API Status: http://{local_ip}:5000/")
        print(f"📱 ESP32 Local Interface: http://[ESP32-IP]/")
        print("")
        print("🎛️ Available Controls:")
        print("   • Water Pump: ON/OFF")
        print("   • Cooling Fan: ON/OFF")
        print("   • Curtain: OPEN/CLOSE")
        print("   • Control Mode: AUTO/MANUAL")
        print("")
        print("📊 Monitored Parameters:")
        print("   • Temperature (°C)")
        print("   • Humidity (%)")
        print("   • pH Level (0-14)")
        print("   • Light Intensity")
        print("   • Soil Moisture (%)")
        print("   • Water Level")
        print("")
        print("🔄 Automatic Features:")
        print("   • Auto irrigation based on soil moisture")
        print("   • Auto fan control based on temperature")
        print("   • Auto curtain control based on light/temperature")
    
    def monitor_system(self):
        """Monitor system processes"""
        while self.running:
            time.sleep(5)
            
            # Check if processes are still running
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} process stopped unexpectedly")
                    self.running = False
                    break
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n\n🛑 Shutdown signal received...")
        self.shutdown()
    
    def shutdown(self):
        """Shutdown all processes"""
        print("🔄 Shutting down Greenhouse System...")
        self.running = False
        
        for name, process in self.processes:
            print(f"   Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Force killing {name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"   ❌ Error stopping {name}: {e}")
        
        print("✅ Greenhouse System shutdown complete")
        sys.exit(0)
    
    def run_system_test(self):
        """Run system test"""
        print("\n🧪 Running System Test...")
        
        if os.path.exists('test_greenhouse_system.py'):
            try:
                subprocess.run([sys.executable, 'test_greenhouse_system.py'], 
                             input='1\n6\n', text=True, timeout=60)
            except subprocess.TimeoutExpired:
                print("   ⚠️  Test timed out")
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        else:
            print("   ⚠️  Test file not found, skipping test")
    
    def start_system(self):
        """Start the complete greenhouse system"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing packages manually.")
            return False
        
        # Check files
        if not self.check_files():
            print("❌ Required files missing. Please ensure all files are present.")
            return False
        
        # Get network info
        local_ip = self.get_network_info()
        
        # Start API server
        if not self.start_api_server():
            return False
        
        # Wait for server to be ready
        if not self.wait_for_server():
            return False
        
        # Show instructions
        self.show_esp32_instructions()
        self.show_usage_instructions(local_ip)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start monitoring
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print("\n✅ Terraponix Greenhouse System is now running!")
        print("   Press Ctrl+C to stop the system")
        print("   Check the web dashboard for real-time monitoring")
        
        # Ask if user wants to run test
        try:
            test_choice = input("\n🧪 Run system test? (y/n): ").strip().lower()
            if test_choice == 'y':
                self.run_system_test()
        except KeyboardInterrupt:
            pass
        
        # Keep running until shutdown
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
        
        return True

def main():
    """Main function"""
    manager = GreenhouseSystemManager()
    
    try:
        success = manager.start_system()
        if not success:
            print("\n❌ Failed to start Greenhouse System")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        manager.shutdown()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        manager.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()