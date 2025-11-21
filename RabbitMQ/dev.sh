#!/bin/bash
# Development helper script for RabbitMQ workers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${GREEN}===================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}===================================================${NC}\n"
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if .env exists
check_env() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_info "Please edit .env with your credentials"
        exit 1
    fi
}

# Check if serviceAccountKey.json exists
check_firebase() {
    if [ ! -f serviceAccountKey.json ]; then
        print_error "serviceAccountKey.json not found!"
        print_info "Please place your Firebase service account key in this directory"
        exit 1
    fi
}

# Install dependencies
install_deps() {
    print_header "Installing Dependencies"
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Run syntax check
check_syntax() {
    print_header "Checking Python Syntax"
    
    echo "Checking worker.py..."
    python -m py_compile worker.py
    
    echo "Checking pipeline modules..."
    for f in src/pipeline/*.py; do
        echo "  - $(basename $f)"
        python -m py_compile "$f"
    done
    
    print_success "All files have valid syntax"
}

# Run a single worker locally
run_worker() {
    print_header "Running Worker Locally"
    check_env
    check_firebase
    
    # Load .env
    set -a
    source .env
    set +a
    
    print_info "Starting worker..."
    python oo.py
}

# Run test publisher
test_publish() {
    print_header "Publishing Test Message"
    check_env
    
    # Load .env
    set -a
    source .env
    set +a
    
    python test_publisher.py
}

# Build Docker image
build_docker() {
    print_header "Building Docker Image"
    docker build -t navnexus-worker:latest .
    print_success "Docker image built successfully"
}

# Run with docker-compose
run_compose() {
    print_header "Running Workers with Docker Compose"
    check_firebase
    
    cd ..
    docker-compose -f docker-compose.workers.yml up --build
}

# Show help
show_help() {
    cat << EOF
RabbitMQ Worker Development Helper

Usage: ./dev.sh [command]

Commands:
    install         Install Python dependencies
    check           Check Python syntax
    worker          Run a single worker locally
    test            Publish a test message to the queue
    build           Build Docker image
    compose         Run all workers with docker-compose
    help            Show this help message

Examples:
    ./dev.sh install        # Install dependencies
    ./dev.sh check          # Check syntax
    ./dev.sh worker         # Run worker locally
    ./dev.sh test           # Send test message
    ./dev.sh compose        # Run all workers in Docker

EOF
}

# Main
case "${1:-help}" in
    install)
        install_deps
        ;;
    check)
        check_syntax
        ;;
    worker)
        run_worker
        ;;
    test)
        test_publish
        ;;
    build)
        build_docker
        ;;
    compose)
        run_compose
        ;;
    help|*)
        show_help
        ;;
esac
