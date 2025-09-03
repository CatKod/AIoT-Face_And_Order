#!/bin/bash

# Stop Production Environment
echo "🛑 Stopping Cafe Face Recognition System - Production Environment"
echo "================================================================="

docker-compose down

echo "✅ Production environment stopped!"
echo ""
echo "💾 Data is preserved in Docker volumes."
echo "🗑️  To remove all data: ./scripts/reset-prod.sh"
