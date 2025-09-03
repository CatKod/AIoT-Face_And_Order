#!/bin/bash

# Stop Development Environment
echo "🛑 Stopping Cafe Face Recognition System - Development Environment"
echo "=================================================================="

docker-compose -f docker-compose.dev.yml down

echo "✅ Development environment stopped!"
echo ""
echo "💾 Data is preserved in Docker volumes."
echo "🗑️  To remove all data: ./scripts/reset-dev.sh"
