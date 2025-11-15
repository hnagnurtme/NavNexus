#!/bin/bash

# Kích hoạt môi trường ảo
echo "Activating virtual environment..."
source /Users/anhnon/NavNexus/RabbitMQ/.venv/bin/activate        

# Tải các biến môi trường từ file .env
# Lệnh này export tất cả các biến trong .env vào phiên shell hiện tại
echo "Loading environment variables from .env..."
set -a
source .env
set +a

# Chạy script Python của bạn
echo "Running Main.py..."
python3 Main.py

# Hủy kích hoạt môi trường ảo sau khi chạy xong
echo "Deactivating virtual environment..."
deactivate