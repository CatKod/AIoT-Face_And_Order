#!/bin/bash

# Start Development Environment
echo "🚀 Starting Cafe Face Recognition System - Development Environment"
echo "================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start development environment
echo "📦 Building and starting development containers..."
docker-compose -f docker-compose.dev.yml up --build

echo "✅ Development environment started!"
echo ""
echo "🌐 Access points:"
echo "   - Main App: http://localhost:5001"
echo "   - pgAdmin: http://localhost:8081 (dev@cafe.com / dev123)"
echo "   - MailHog: http://localhost:8025"
echo "   - PostgreSQL: localhost:5433"
echo "   - Redis: localhost:6380"
echo ""
echo "🛑 To stop: Ctrl+C or run './scripts/stop-dev.sh'"
