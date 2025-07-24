#!/usr/bin/env python3
"""
Terraponix Greenhouse System Test Client
This script tests the complete greenhouse automation system
"""

import requests
import json
import time
import random
from datetime import datetime

class GreenhouseTestClient:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url.rstrip('/')
        self.device_id = "test_greenhouse_esp32"
        
    def test_connection(self):
        """Test API server connection"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ API Server Connection: OK")
                print(f"   Server: {data.get('message')}")
                print(f"   Version: {data.get('version')}")
                print(f"   Active Devices: {data.get('active_devices')}")
                return True
            else:
                print("❌ API Server Connection: Failed")
                return False
        except Exception as e:
            print(f"❌ API Server Connection Error: {e}")
            return False
    
    def register_device(self):
        """Register test device with server"""
        try:
            payload = {
                "device_id": self.device_id,
                "device_type": "greenhouse_controller",
                "ip_address": "192.168.1.100",
                "capabilities": "temperature,humidity,ph,light,water_level,soil_moisture,pump,fan,curtain"
            }
            
            response = requests.post(
                f"{self.server_url}/api/register",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Device Registration: OK")
                print(f"   Device ID: {data.get('device_id')}")
                return True
            else:
                print(f"❌ Device Registration Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Device Registration Error: {e}")
            return False
    
    def generate_sensor_data(self):
        """Generate realistic sensor data"""
        return {
            "device_id": self.device_id,
            "timestamp": int(time.time() * 1000),
            "temperature": round(random.uniform(20.0, 35.0), 1),
            "humidity": round(random.uniform(40.0, 80.0), 1),
            "ph": round(random.uniform(6.0, 8.0), 2),
            "light_intensity": random.randint(100, 4000),
            "water_level": random.randint(500, 2000),
            "water_status": random.choice(["OK", "LOW"]),
            "soil_moisture": random.randint(20, 90),
            "curtain_status": random.choice(["OPEN", "CLOSED"]),
            "pump_status": random.choice(["ON", "OFF"]),
            "fan_status": random.choice(["ON", "OFF"]),
            "mode": random.choice(["AUTO", "MANUAL"]),
            "wifi_status": "CONNECTED",
            "ip_address": "192.168.1.100",
            "wifi_signal": random.randint(-80, -30)
        }
    
    def send_sensor_data(self, data=None):
        """Send sensor data to server"""
        try:
            if data is None:
                data = self.generate_sensor_data()
            
            response = requests.post(
                f"{self.server_url}/api/greenhouse-data",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Sensor Data Sent: OK")
                print(f"   Temperature: {data['temperature']}°C")
                print(f"   Humidity: {data['humidity']}%")
                print(f"   pH: {data['ph']}")
                print(f"   Soil Moisture: {data['soil_moisture']}%")
                return True
            else:
                print(f"❌ Send Sensor Data Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Send Sensor Data Error: {e}")
            return False
    
    def get_status(self):
        """Get current greenhouse status"""
        try:
            response = requests.get(
                f"{self.server_url}/api/greenhouse/status",
                params={"device_id": self.device_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Status Retrieved: OK")
                if data['status'] == 'success':
                    sensor_data = data['data']
                    print(f"   Last Update: {sensor_data['timestamp']}")
                    print(f"   Temperature: {sensor_data['temperature']}°C")
                    print(f"   Pump Status: {sensor_data['pump_status']}")
                    print(f"   Fan Status: {sensor_data['fan_status']}")
                    print(f"   Mode: {sensor_data['mode']}")
                return True
            else:
                print(f"❌ Get Status Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get Status Error: {e}")
            return False
    
    def send_control_command(self, device, value):
        """Send control command to device"""
        try:
            payload = {
                "device_id": self.device_id,
                "device": device,
                "value": value
            }
            
            response = requests.post(
                f"{self.server_url}/api/greenhouse-control",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Control Command Sent: {device} = {value}")
                return True
            else:
                print(f"❌ Control Command Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Control Command Error: {e}")
            return False
    
    def get_history(self, hours=1):
        """Get historical data"""
        try:
            response = requests.get(
                f"{self.server_url}/api/greenhouse/history",
                params={
                    "device_id": self.device_id,
                    "hours": hours,
                    "limit": 10
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ History Retrieved: {data['total_records']} records")
                return True
            else:
                print(f"❌ Get History Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get History Error: {e}")
            return False
    
    def run_full_system_test(self):
        """Run complete system test"""
        print("🧪 Starting Terraponix Greenhouse System Test")
        print("=" * 50)
        
        # Test 1: Connection
        print("\n1️⃣ Testing API Connection...")
        if not self.test_connection():
            print("❌ Test Failed: Cannot connect to API server")
            return False
        
        # Test 2: Device Registration
        print("\n2️⃣ Testing Device Registration...")
        if not self.register_device():
            print("❌ Test Failed: Cannot register device")
            return False
        
        # Test 3: Send Sensor Data
        print("\n3️⃣ Testing Sensor Data Transmission...")
        for i in range(3):
            print(f"   Sending data packet {i+1}/3...")
            if not self.send_sensor_data():
                print("❌ Test Failed: Cannot send sensor data")
                return False
            time.sleep(1)
        
        # Test 4: Get Status
        print("\n4️⃣ Testing Status Retrieval...")
        if not self.get_status():
            print("❌ Test Failed: Cannot get status")
            return False
        
        # Test 5: Control Commands
        print("\n5️⃣ Testing Control Commands...")
        commands = [
            ("pump", True),
            ("fan", True),
            ("curtain", False),
            ("pump", False),
            ("fan", False)
        ]
        
        for device, value in commands:
            if not self.send_control_command(device, value):
                print(f"❌ Test Failed: Cannot control {device}")
                return False
            time.sleep(0.5)
        
        # Test 6: Historical Data
        print("\n6️⃣ Testing Historical Data...")
        if not self.get_history():
            print("❌ Test Failed: Cannot get history")
            return False
        
        print("\n✅ All Tests Passed!")
        print("🎉 Terraponix Greenhouse System is working correctly!")
        print("\n📊 Next Steps:")
        print("   1. Upload the ESP32 code to your device")
        print("   2. Update WiFi credentials and server IP in the code")
        print("   3. Start the greenhouse_api.py server")
        print("   4. Access the dashboard at http://your-server-ip:5000/dashboard")
        print("   5. Monitor your greenhouse remotely!")
        
        return True
    
    def simulate_continuous_monitoring(self, duration_minutes=5):
        """Simulate continuous greenhouse monitoring"""
        print(f"\n🔄 Starting {duration_minutes}-minute simulation...")
        print("   (Press Ctrl+C to stop)")
        
        try:
            end_time = time.time() + (duration_minutes * 60)
            packet_count = 0
            
            while time.time() < end_time:
                packet_count += 1
                print(f"\n📡 Sending data packet #{packet_count}")
                
                # Generate and send realistic data
                data = self.generate_sensor_data()
                if self.send_sensor_data(data):
                    print("   ✅ Data sent successfully")
                else:
                    print("   ❌ Failed to send data")
                
                # Random control commands
                if random.random() < 0.3:  # 30% chance
                    device = random.choice(["pump", "fan", "curtain"])
                    value = random.choice([True, False])
                    print(f"   🎛️ Sending control command: {device} = {value}")
                    self.send_control_command(device, value)
                
                # Wait before next transmission
                time.sleep(10)  # Send data every 10 seconds
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Simulation stopped by user")
        
        print(f"\n📊 Simulation completed: {packet_count} data packets sent")

def main():
    """Main function"""
    print("🌱 Terraponix Greenhouse System Test Client")
    print("=" * 50)
    
    # Get server URL from user
    server_url = input("Enter server URL (default: http://localhost:5000): ").strip()
    if not server_url:
        server_url = "http://localhost:5000"
    
    # Create test client
    client = GreenhouseTestClient(server_url)
    
    while True:
        print("\n🎯 Test Options:")
        print("1. Run Full System Test")
        print("2. Send Single Sensor Data")
        print("3. Get Current Status")
        print("4. Send Control Command")
        print("5. Start Continuous Simulation")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            client.run_full_system_test()
        
        elif choice == '2':
            client.send_sensor_data()
        
        elif choice == '3':
            client.get_status()
        
        elif choice == '4':
            device = input("Device (pump/fan/curtain): ").strip()
            value_str = input("Value (on/off or true/false): ").strip().lower()
            value = value_str in ['on', 'true', '1', 'yes']
            client.send_control_command(device, value)
        
        elif choice == '5':
            duration = input("Simulation duration in minutes (default: 5): ").strip()
            duration = int(duration) if duration.isdigit() else 5
            client.simulate_continuous_monitoring(duration)
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()