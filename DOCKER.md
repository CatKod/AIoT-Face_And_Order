# Cafe Face Recognition System - Docker Quick Reference

## 🚀 Quick Commands

### Development
```bash
# Start development
./scripts/start-dev.sh

# Stop development  
./scripts/stop-dev.sh

# Reset development (removes all data)
./scripts/reset-dev.sh
```

### Production
```bash
# Start production
./scripts/start-prod.sh

# Stop production
./scripts/stop-prod.sh  

# Reset production (removes all data)
./scripts/reset-prod.sh
```

## 🌐 Access Points

### Development Environment
- **Main App**: http://localhost:5000
- **pgAdmin**: http://localhost:8080 (admin@cafe.local / admin123)
- **MailHog**: http://localhost:8025

### Production Environment  
- **Main App**: http://localhost
- **pgAdmin**: http://localhost:8080 (admin@cafe.local / admin123)
- **Grafana**: http://localhost:3000 (admin / admin)
- **Prometheus**: http://localhost:9090

## 🔧 Troubleshooting

### Check Service Status
```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]
```

### Common Issues
```bash
# Port already in use
netstat -tulpn | grep :5000

# Database connection issues
docker logs cafe_postgres

# Check face recognition
docker exec -it cafe_app python -c "import cv2; print('OpenCV OK')"
```

## 💾 Backup & Restore

### Database Backup
```bash
# Backup
docker exec cafe_postgres pg_dump -U cafe_admin cafe_face_recognition > backup.sql

# Restore  
docker exec -i cafe_postgres psql -U cafe_admin cafe_face_recognition < backup.sql
```

### Face Data Backup
```bash
# Backup face images
docker cp cafe_app:/app/data/faces ./faces_backup

# Restore face images
docker cp ./faces_backup cafe_app:/app/data/faces
```

## 🔐 Default Credentials

### Database
- **User**: cafe_admin
- **Password**: secure_cafe_password
- **Database**: cafe_face_recognition

### pgAdmin
- **Email**: admin@cafe.local  
- **Password**: admin123

### Grafana (Production)
- **User**: admin
- **Password**: admin

⚠️ **Change these credentials in production!**

## 📱 API Endpoints

### Face Recognition
- `POST /api/recognize` - Recognize face in image
- `GET /recognize` - Live recognition page

### Customer Management  
- `GET /api/customers` - List customers
- `POST /api/customers` - Add customer
- `GET /customers/{id}` - Customer details

### Orders & Menu
- `GET /api/orders` - List orders
- `POST /api/orders` - Create order  
- `GET /api/menu` - Menu items
- `POST /api/menu` - Add menu item

### Recommendations
- `GET /api/recommendations/{customer_id}` - Get personalized recommendations

## 🎯 System Requirements

### Minimum
- **RAM**: 4GB
- **Storage**: 10GB  
- **CPU**: 2 cores
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Recommended
- **RAM**: 8GB+
- **Storage**: 50GB+
- **CPU**: 4+ cores
- **GPU**: Optional (for faster face recognition)

## 🔄 Update System

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart services
./scripts/stop-dev.sh && ./scripts/start-dev.sh
```

## 📊 Monitoring

### Health Checks
```bash
# Check application health
curl http://localhost:5000/health

# Check database connection  
docker exec cafe_postgres pg_isready -U cafe_admin

# Check Redis
docker exec cafe_redis redis-cli ping
```

### Performance
- **Grafana Dashboards**: http://localhost:3000
- **Prometheus Metrics**: http://localhost:9090  
- **Application Logs**: `docker logs cafe_app`

---
📖 **Full documentation**: See README.md for complete setup guide
