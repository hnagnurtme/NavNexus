#!/bin/bash

# Start script to run both worker and healthcheck API
# This script runs both processes concurrently

echo "Starting RabbitMQ Worker and Health Check API..."

# Start health check API in background
echo "Starting Health Check API on port 8000..."
python healthcheck_api.py &
HEALTHCHECK_PID=$!

# Wait a bit for healthcheck to start
sleep 2

# Start worker in foreground
echo "Starting RabbitMQ Worker..."
python worker.py &
WORKER_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down gracefully..."
    kill -SIGTERM $WORKER_PID 2>/dev/null
    kill -SIGTERM $HEALTHCHECK_PID 2>/dev/null
    wait $WORKER_PID
    wait $HEALTHCHECK_PID
    echo "Shutdown complete"
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for both processes
wait -n

# If one process exits, kill the other
exit_code=$?
echo "One process exited with code $exit_code, shutting down..."
shutdown
