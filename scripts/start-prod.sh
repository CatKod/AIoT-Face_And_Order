#!/bin/bash

# Start Production Environment
echo "🚀 Starting Cafe Face Recognition System - Production Environment"
echo "=================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Load production environment variables
if [ -f .env.production ]; then
    echo "📄 Loading production environment variables..."
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Build and start production environment
echo "📦 Building and starting production containers..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are healthy
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Production environment started!"
echo ""
echo "🌐 Access points:"
echo "   - Main App: http://localhost"
echo "   - pgAdmin: http://localhost:8080 (admin@cafe.com / admin123)"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin / grafana_password)"
echo "   - Direct App: http://localhost:5000"
echo ""
echo "📊 Monitoring:"
echo "   - Application logs: docker-compose logs -f cafe_app"
echo "   - All logs: docker-compose logs -f"
echo ""
echo "🛑 To stop: ./scripts/stop-prod.sh"
