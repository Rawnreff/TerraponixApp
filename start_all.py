#!/usr/bin/env python3
"""
Script untuk menjalankan semua komponen sensor API sekaligus
Berguna untuk testing dan demo
"""

import subprocess
import time
import threading
import os
import signal
import sys
import requests
from datetime import datetime

class MultiProcessRunner:
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def run_command(self, name, command, delay=0):
        """Jalankan command dalam subprocess terpisah"""
        if delay > 0:
            time.sleep(delay)
            
        try:
            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes[name] = process
            
            # Monitor output
            while self.running and process.poll() is None:
                output = process.stdout.readline()
                if output:
                    print(f"[{name}] {output.strip()}")
                    
        except Exception as e:
            print(f"❌ Error starting {name}: {e}")
    
    def stop_all(self):
        """Hentikan semua proses"""
        self.running = False
        print("\n🛑 Stopping all processes...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 {name} killed (force)")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")

def check_dependencies():
    """Cek apakah semua dependencies terinstall"""
    print("🔍 Checking dependencies...")
    
    try:
        import flask
        import requests
        print("✅ Flask and requests are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def wait_for_api(url, timeout=30):
    """Tunggu hingga API server siap"""
    print(f"⏳ Waiting for API server at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ API server is ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print("❌ API server not responding")
    return False

def get_local_ip():
    """Dapatkan IP address lokal"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def main():
    print("=" * 60)
    print("🚀 SENSOR API - MULTI-PROCESS LAUNCHER")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cek dependencies
    if not check_dependencies():
        return
    
    # Dapatkan IP lokal
    local_ip = get_local_ip()
    api_url = f"http://{local_ip}:5000"
    
    print(f"🌐 Local IP: {local_ip}")
    print(f"📡 API URL: {api_url}")
    print()
    
    # Setup signal handler untuk cleanup
    runner = MultiProcessRunner()
    
    def signal_handler(sig, frame):
        print(f"\n🛑 Received signal {sig}")
        runner.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. Start API Server
        api_thread = threading.Thread(
            target=runner.run_command,
            args=("API-Server", "python sensor_api.py", 0)
        )
        api_thread.daemon = True
        api_thread.start()
        
        # 2. Tunggu API siap
        if not wait_for_api(api_url):
            print("❌ Cannot start without API server")
            return
        
        # 3. Start Sensor Client (Temperature)
        sensor_thread = threading.Thread(
            target=runner.run_command,
            args=("Sensor-Client", f"python sensor_client.py", 3)
        )
        sensor_thread.daemon = True
        sensor_thread.start()
        
        print("\n" + "=" * 60)
        print("🎉 ALL SERVICES STARTED!")
        print("=" * 60)
        print(f"📡 API Server: {api_url}")
        print(f"🌡️ Sensor Client: Sending temperature data")
        print("📱 You can now run: python app_client.py")
        print()
        print("💡 Instructions:")
        print("   1. API server is running and ready")
        print("   2. Temperature sensor is sending data every 5 seconds")
        print("   3. Open another terminal and run: python app_client.py")
        print("   4. Edit client files to change API_URL if needed")
        print()
        print("🛑 Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep main thread alive
        while runner.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Received Ctrl+C")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        runner.stop_all()
        print("👋 All services stopped. Goodbye!")

if __name__ == "__main__":
    main()