#!/bin/bash

# Reset Development Environment
echo "🗑️  Resetting Cafe Face Recognition System - Development Environment"
echo "==================================================================="

read -p "⚠️  This will remove ALL development data. Are you sure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing development containers and volumes..."
    docker-compose -f docker-compose.dev.yml down -v --remove-orphans
    
    echo "🗑️  Removing development images..."
    docker-compose -f docker-compose.dev.yml down --rmi local
    
    echo "✅ Development environment reset complete!"
    echo "🚀 Run './scripts/start-dev.sh' to start fresh."
else
    echo "❌ Reset cancelled."
fi
