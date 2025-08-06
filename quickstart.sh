#!/bin/bash

# NetBox Orchestrator POC Quick Start Script
# This script automates the initial setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Header
echo "================================================="
echo "    NetBox Orchestrator POC Quick Start"
echo "================================================="
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

print_success "All prerequisites are installed!"

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Docker daemon is running!"

# Check available resources
print_status "Checking system resources..."

# Check available memory (should be at least 4GB)
available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
if (( $(echo "$available_memory < 4" | bc -l) )); then
    print_warning "Available memory is ${available_memory}GB. Recommended: 8GB or more."
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Available memory: ${available_memory}GB"
fi

# Check available disk space (should be at least 10GB)
available_space=$(df . | tail -1 | awk '{print $4}')
available_space_gb=$((available_space / 1024 / 1024))
if [ $available_space_gb -lt 10 ]; then
    print_warning "Available disk space is ${available_space_gb}GB. Recommended: 20GB or more."
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Available disk space: ${available_space_gb}GB"
fi

# Setup environment
print_status "Setting up environment..."

if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created! Please customize it if needed."
else
    print_status ".env file already exists."
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
if command_exists pip3; then
    pip3 install -r requirements.txt
elif command_exists pip; then
    pip install -r requirements.txt
else
    print_error "pip is not available. Please install pip."
    exit 1
fi

print_success "Python dependencies installed!"

# Check for port conflicts
print_status "Checking for port conflicts..."

check_port() {
    local port=$1
    local service=$2
    
    if ss -tulpn | grep -q ":$port "; then
        print_warning "Port $port is already in use (needed for $service)"
        print_status "You may need to stop other services or change configuration"
        return 1
    else
        print_success "Port $port is available for $service"
        return 0
    fi
}

port_conflicts=0
check_port 8000 "NetBox" || port_conflicts=$((port_conflicts + 1))
check_port 8080 "Orchestrator API" || port_conflicts=$((port_conflicts + 1))
check_port 3000 "Orchestrator UI" || port_conflicts=$((port_conflicts + 1))
check_port 5432 "PostgreSQL" || port_conflicts=$((port_conflicts + 1))

if [ $port_conflicts -gt 0 ]; then
    print_warning "$port_conflicts port(s) are already in use."
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Please stop conflicting services or modify docker-compose.yml port mappings."
        exit 1
    fi
fi

# Start NetBox services
print_status "Starting NetBox services..."
cd netbox
docker-compose pull
docker-compose up -d
cd ..

print_success "NetBox services started!"

# Wait for NetBox to be ready
wait_for_service "http://localhost:8000/api/" "NetBox"

# Start Orchestrator services
print_status "Starting Orchestrator services..."
cd example-orchestrator
docker-compose pull
docker-compose up -d
cd ..

print_success "Orchestrator services started!"

# Wait for Orchestrator to be ready
wait_for_service "http://localhost:8080/health" "Orchestrator API"
wait_for_service "http://localhost:3000" "Orchestrator UI"

# Import device types
print_status "Importing device types..."
if python3 device_import.py; then
    print_success "Device types imported successfully!"
else
    print_warning "Device import encountered some issues, but services are running."
fi

# Final health check
print_status "Performing final health check..."

services_ok=0
total_services=3

# Check NetBox
if curl -s http://localhost:8000/api/ > /dev/null; then
    print_success "✓ NetBox is responding (http://localhost:8000)"
    services_ok=$((services_ok + 1))
else
    print_error "✗ NetBox is not responding"
fi

# Check Orchestrator API
if curl -s http://localhost:8080/health > /dev/null; then
    print_success "✓ Orchestrator API is responding (http://localhost:8080)"
    services_ok=$((services_ok + 1))
else
    print_error "✗ Orchestrator API is not responding"
fi

# Check Orchestrator UI
if curl -s http://localhost:3000 > /dev/null; then
    print_success "✓ Orchestrator UI is responding (http://localhost:3000)"
    services_ok=$((services_ok + 1))
else
    print_error "✗ Orchestrator UI is not responding"
fi

echo ""
echo "================================================="
echo "           Setup Complete!"
echo "================================================="
echo ""

if [ $services_ok -eq $total_services ]; then
    print_success "All services are running successfully!"
    echo ""
    echo "🌐 Access your services:"
    echo "   • NetBox:           http://localhost:8000"
    echo "   • Orchestrator UI:  http://localhost:3000"
    echo "   • Orchestrator API: http://localhost:8080"
    echo ""
    echo "📚 Default credentials:"
    echo "   • NetBox: admin / admin (change immediately!)"
    echo ""
    echo "🛠️  Useful commands:"
    echo "   • View logs:        make logs"
    echo "   • Stop services:    make stop"
    echo "   • Restart:          make restart"
    echo "   • Health check:     make health"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
    print_success "Enjoy your NetBox Orchestrator POC!"
else
    print_warning "Some services may not be fully ready yet."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   • Check logs:       make logs"
    echo "   • Check containers: docker ps"
    echo "   • Restart services: make restart"
    echo ""
    echo "📖 For more help, see README.md troubleshooting section"
fi

echo ""
echo "================================================="
