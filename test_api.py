#!/usr/bin/env python3
"""
Script untuk testing API endpoints
Memastikan semua fungsi berjalan dengan baik
"""

import requests
import json
import time
import random
from datetime import datetime

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.test_results = {}
        
    def test_endpoint(self, name, method, endpoint, data=None, expected_status=200):
        """Test single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"🧪 Testing {name}...")
            print(f"   {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=5)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check status code
            if response.status_code == expected_status:
                print(f"   ✅ Status: {response.status_code}")
                
                # Try to parse JSON
                try:
                    result = response.json()
                    print(f"   📄 Response: {json.dumps(result, indent=2)[:200]}...")
                    self.test_results[name] = {'status': 'PASS', 'response': result}
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
                    self.test_results[name] = {'status': 'PASS', 'response': response.text}
            else:
                print(f"   ❌ Status: {response.status_code} (expected {expected_status})")
                print(f"   📄 Response: {response.text}")
                self.test_results[name] = {'status': 'FAIL', 'response': response.text}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results[name] = {'status': 'ERROR', 'error': str(e)}
        
        print()
        time.sleep(1)
    
    def run_full_test_suite(self):
        """Jalankan semua test"""
        print("=" * 60)
        print("🔬 SENSOR API - COMPREHENSIVE TESTING")
        print("=" * 60)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: API Status
        self.test_endpoint(
            "API Status",
            "GET",
            "/"
        )
        
        # Test 2: Register Temperature Sensor
        self.test_endpoint(
            "Register Temperature Sensor",
            "POST",
            "/api/sensor/register",
            {
                "sensor_id": "TEST_TEMP_001",
                "sensor_type": "temperature",
                "sensor_name": "Test Temperature Sensor"
            }
        )
        
        # Test 3: Register Humidity Sensor
        self.test_endpoint(
            "Register Humidity Sensor",
            "POST",
            "/api/sensor/register",
            {
                "sensor_id": "TEST_HUM_001", 
                "sensor_type": "humidity",
                "sensor_name": "Test Humidity Sensor"
            }
        )
        
        # Test 4: Send Temperature Data
        temp_value = round(random.uniform(20.0, 35.0), 2)
        self.test_endpoint(
            "Send Temperature Data",
            "POST",
            "/api/sensor/data",
            {
                "sensor_id": "TEST_TEMP_001",
                "sensor_type": "temperature",
                "value": temp_value,
                "unit": "°C"
            }
        )
        
        # Test 5: Send Humidity Data
        hum_value = round(random.uniform(40.0, 90.0), 2)
        self.test_endpoint(
            "Send Humidity Data",
            "POST",
            "/api/sensor/data",
            {
                "sensor_id": "TEST_HUM_001",
                "sensor_type": "humidity",
                "value": hum_value,
                "unit": "%"
            }
        )
        
        # Test 6: Get Specific Sensor Data
        self.test_endpoint(
            "Get Temperature Sensor Data",
            "GET",
            "/api/sensor/data/TEST_TEMP_001"
        )
        
        # Test 7: Get All Sensors Data
        self.test_endpoint(
            "Get All Sensors Data",
            "GET",
            "/api/sensors/all"
        )
        
        # Test 8: Get Sensor History
        self.test_endpoint(
            "Get Sensor History",
            "GET",
            "/api/sensor/history/TEST_TEMP_001?limit=5"
        )
        
        # Test 9: Get API Status
        self.test_endpoint(
            "Get API Status",
            "GET",
            "/api/sensor/status"
        )
        
        # Test 10: Invalid Sensor ID (should fail)
        self.test_endpoint(
            "Get Invalid Sensor (Expected Fail)",
            "GET",
            "/api/sensor/data/INVALID_SENSOR",
            expected_status=404
        )
        
        # Test 11: Invalid Data Format (should fail)
        self.test_endpoint(
            "Send Invalid Data (Expected Fail)",
            "POST",
            "/api/sensor/data",
            {
                "sensor_id": "TEST_INVALID",
                # Missing sensor_type and value
            },
            expected_status=400
        )
        
        # Summary
        self.print_test_summary()
    
    def run_load_test(self, duration=30):
        """Test performa dengan multiple requests"""
        print("=" * 60)
        print("⚡ LOAD TESTING")
        print("=" * 60)
        print(f"⏰ Duration: {duration} seconds")
        print("🔄 Sending requests every 1 second...")
        print()
        
        start_time = time.time()
        request_count = 0
        success_count = 0
        
        while time.time() - start_time < duration:
            try:
                # Send random sensor data
                temp_value = round(random.uniform(20.0, 35.0), 2)
                response = requests.post(
                    f"{self.base_url}/api/sensor/data",
                    json={
                        "sensor_id": "LOAD_TEST_SENSOR",
                        "sensor_type": "temperature",
                        "value": temp_value,
                        "unit": "°C"
                    },
                    timeout=5
                )
                
                request_count += 1
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ Request {request_count}: {temp_value}°C")
                else:
                    print(f"❌ Request {request_count}: Failed ({response.status_code})")
                
            except Exception as e:
                request_count += 1
                print(f"❌ Request {request_count}: Error ({e})")
            
            time.sleep(1)
        
        # Load test summary
        success_rate = (success_count / request_count * 100) if request_count > 0 else 0
        print(f"\n📊 Load Test Results:")
        print(f"   Total requests: {request_count}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {request_count - success_count}")
        print(f"   Success rate: {success_rate:.1f}%")
    
    def print_test_summary(self):
        """Print summary of all tests"""
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results.values() if r['status'] == 'ERROR'])
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        # Detail results
        for test_name, result in self.test_results.items():
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌', 
                'ERROR': '🔥'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {test_name}: {result['status']}")
        
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! API is working perfectly!")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ Most tests passed, but some issues found.")
        else:
            print("🚨 Multiple tests failed. Please check API server.")
        
        print("=" * 60)

def main():
    # Configuration
    API_URL = "http://localhost:5000"  # Ganti sesuai IP server Anda
    
    print("🔬 API Tester - Sensor API Testing Suite")
    print(f"🌐 Target URL: {API_URL}")
    print()
    
    # Check if API is reachable
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            print("✅ API server is reachable!")
        else:
            print(f"⚠️ API server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach API server: {e}")
        print("💡 Make sure the API server is running:")
        print("   python sensor_api.py")
        return
    
    print()
    
    # Menu
    print("Choose test mode:")
    print("1. Full Test Suite (comprehensive testing)")
    print("2. Load Test (performance testing)")
    print("3. Both (full suite + load test)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    tester = APITester(API_URL)
    
    if choice == "1":
        tester.run_full_test_suite()
    elif choice == "2":
        duration = input("Load test duration in seconds (default 30): ").strip()
        duration = int(duration) if duration.isdigit() else 30
        tester.run_load_test(duration)
    elif choice == "3":
        tester.run_full_test_suite()
        print("\n" + "="*60)
        print("🔄 Starting Load Test...")
        time.sleep(2)
        duration = input("Load test duration in seconds (default 30): ").strip()
        duration = int(duration) if duration.isdigit() else 30
        tester.run_load_test(duration)
    else:
        print("❌ Invalid choice")
        return
    
    print("\n👋 Testing completed!")

if __name__ == "__main__":
    main()