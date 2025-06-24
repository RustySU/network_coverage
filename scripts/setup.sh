#!/bin/bash

# Mobile Coverage API Setup Script
# This script sets up the complete development environment using Docker

set -e

echo "🚀 Setting up Mobile Coverage API..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
make docker-build

echo "🔧 Starting services..."
make docker-up

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️ Running database migrations..."
make migrate

# Load data
echo "📊 Loading CSV data..."
make load-preprocessed

echo "✅ Setup complete!"
echo ""
echo "🎉 Your Mobile Coverage API is ready!"
echo ""
echo "📋 Available commands:"
echo "  make test          - Run tests"
echo "  make lint          - Run linter"
echo "  make format        - Format code"
echo "  make check-all     - Run all quality checks"
echo "  make shell         - Open shell in container"
echo "  make docker-logs   - View logs"
echo ""
echo "🌐 Access the API:"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Root Endpoint: http://localhost:8000/"
echo "  - Network Coverage: http://localhost:8000/api/v1/network-coverage"
echo ""
echo "🔧 To stop services: make docker-down" 