#!/bin/bash

# Script Quick Start untuk API Sensor dengan Hotspot Seluler
# Dibuat untuk memudahkan setup dan penggunaan

echo "🚀 API SENSOR - QUICK START"
echo "=============================="
echo

# Function untuk menampilkan banner
show_banner() {
    echo "📡 API Konektivitas Sensor - Hotspot Seluler"
    echo "✨ Setup komunikasi sensor dan aplikasi melalui hotspot"
    echo
}

# Function untuk mendapatkan IP address
get_local_ip() {
    # Mencoba berbagai cara untuk mendapatkan IP
    if command -v ip >/dev/null 2>&1; then
        ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}'
    elif command -v ifconfig >/dev/null 2>&1; then
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1
    else
        echo "localhost"
    fi
}

# Function untuk check dependencies
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Check Python3
    if ! command -v python3 >/dev/null 2>&1; then
        echo "❌ Python3 tidak ditemukan. Install dengan: sudo apt install python3"
        exit 1
    fi
    
    # Check Flask
    if ! python3 -c "import flask" 2>/dev/null; then
        echo "❌ Flask tidak ditemukan. Install dengan: sudo apt install python3-flask"
        exit 1
    fi
    
    # Check requests
    if ! python3 -c "import requests" 2>/dev/null; then
        echo "❌ Requests tidak ditemukan. Install dengan: sudo apt install python3-requests"
        exit 1
    fi
    
    echo "✅ Semua dependencies tersedia!"
    echo
}

# Function untuk show menu
show_menu() {
    echo "Pilih mode operasi:"
    echo "1. 🖥️  Start API Server (untuk perangkat yang jadi server)"
    echo "2. 📡 Start Sensor Client (untuk perangkat sensor)"
    echo "3. 📱 Start App Client (untuk perangkat aplikasi)"
    echo "4. 🔬 Test API (untuk testing endpoint)"
    echo "5. 🚀 Start All (API + Sensor simulasi)"
    echo "6. 📋 Show Network Info"
    echo "7. 📚 Show Documentation"
    echo "0. ❌ Exit"
    echo
}

# Function untuk network info
show_network_info() {
    echo "🌐 INFORMASI JARINGAN"
    echo "====================="
    LOCAL_IP=$(get_local_ip)
    echo "📍 IP Address lokal: $LOCAL_IP"
    echo "🔗 URL API Server: http://$LOCAL_IP:5000"
    echo
    echo "💡 Langkah setup hotspot:"
    echo "   1. Aktifkan hotspot di smartphone"
    echo "   2. Hubungkan semua perangkat ke hotspot yang sama"
    echo "   3. Catat IP address perangkat server: $LOCAL_IP"
    echo "   4. Update IP di file sensor_client.py dan app_client.py"
    echo "   5. Jalankan komponen sesuai kebutuhan"
    echo
}

# Function untuk show documentation
show_documentation() {
    echo "📚 DOKUMENTASI SINGKAT"
    echo "======================"
    echo
    echo "🔧 File Utama:"
    echo "   sensor_api.py     - API server (jalani di 1 perangkat)"
    echo "   sensor_client.py  - Client sensor (jalani di perangkat sensor)"
    echo "   app_client.py     - Client aplikasi (jalani di perangkat app)"
    echo "   test_api.py       - Testing tool"
    echo
    echo "🌐 Endpoint API:"
    echo "   GET  /                        - Status API"
    echo "   POST /api/sensor/register     - Registrasi sensor"
    echo "   POST /api/sensor/data         - Kirim data sensor"
    echo "   GET  /api/sensor/data/<id>    - Ambil data sensor"
    echo "   GET  /api/sensors/all         - Ambil semua data"
    echo "   GET  /api/sensor/status       - Status konektivitas"
    echo
    echo "📖 Lihat README.md untuk dokumentasi lengkap"
    echo
}

# Function untuk start API server
start_api_server() {
    echo "🚀 Starting API Server..."
    LOCAL_IP=$(get_local_ip)
    echo "📡 Server akan berjalan di: http://$LOCAL_IP:5000"
    echo "🛑 Tekan Ctrl+C untuk stop"
    echo
    python3 sensor_api.py
}

# Function untuk start sensor client
start_sensor_client() {
    echo "📡 Starting Sensor Client..."
    LOCAL_IP=$(get_local_ip)
    echo "💡 Pastikan sudah update IP di sensor_client.py ke: http://$LOCAL_IP:5000"
    echo "🛑 Tekan Ctrl+C untuk stop"
    echo
    read -p "Lanjutkan? (y/n): " confirm
    if [[ $confirm == [yY] ]]; then
        python3 sensor_client.py
    fi
}

# Function untuk start app client
start_app_client() {
    echo "📱 Starting App Client..."
    LOCAL_IP=$(get_local_ip)
    echo "💡 Pastikan sudah update IP di app_client.py ke: http://$LOCAL_IP:5000"
    echo
    read -p "Lanjutkan? (y/n): " confirm
    if [[ $confirm == [yY] ]]; then
        python3 app_client.py
    fi
}

# Function untuk test API
test_api() {
    echo "🔬 Starting API Test..."
    LOCAL_IP=$(get_local_ip)
    echo "💡 Pastikan API server sudah berjalan di: http://$LOCAL_IP:5000"
    echo
    read -p "Lanjutkan? (y/n): " confirm
    if [[ $confirm == [yY] ]]; then
        python3 test_api.py
    fi
}

# Function untuk start all
start_all() {
    echo "🚀 Starting All Components..."
    echo "💡 Ini akan menjalankan API server + simulasi sensor"
    echo "🛑 Tekan Ctrl+C untuk stop semua"
    echo
    read -p "Lanjutkan? (y/n): " confirm
    if [[ $confirm == [yY] ]]; then
        python3 start_all.py
    fi
}

# Main script
main() {
    show_banner
    check_dependencies
    
    while true; do
        show_menu
        read -p "Masukkan pilihan (0-7): " choice
        echo
        
        case $choice in
            1)
                start_api_server
                ;;
            2)
                start_sensor_client
                ;;
            3)
                start_app_client
                ;;
            4)
                test_api
                ;;
            5)
                start_all
                ;;
            6)
                show_network_info
                read -p "Tekan Enter untuk kembali ke menu..."
                ;;
            7)
                show_documentation
                read -p "Tekan Enter untuk kembali ke menu..."
                ;;
            0)
                echo "👋 Terima kasih! Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Pilihan tidak valid. Coba lagi."
                ;;
        esac
        echo
    done
}

# Jalankan script utama
main