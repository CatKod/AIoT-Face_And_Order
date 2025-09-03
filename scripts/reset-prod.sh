#!/bin/bash

# Reset Production Environment
echo "🗑️  Resetting Cafe Face Recognition System - Production Environment"
echo "=================================================================="

read -p "⚠️  This will remove ALL production data. Are you sure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing production containers and volumes..."
    docker-compose down -v --remove-orphans
    
    echo "🗑️  Removing production images..."
    docker-compose down --rmi local
    
    echo "✅ Production environment reset complete!"
    echo "🚀 Run './scripts/start-prod.sh' to start fresh."
else
    echo "❌ Reset cancelled."
fi
