# PostgreSQL Handle.Net Server Setup

This directory contains a PostgreSQL-based Handle.Net server configuration that allows direct database manipulation, bypassing the Global Handle Registry (GHR) dependency limitations found in the Berkeley DB approach.

## Overview

The PostgreSQL setup provides:
- SQL-based storage backend for Handle.Net Server 9.3.1
- Direct database access for admin handle creation
- Independent operation without GHR dependencies
- Web-based administration interface

## Files

- `docker-compose.yml` - PostgreSQL and Handle Server configuration
- `create-scripts/init_db.sql` - PostgreSQL database schema and admin handle initialization
- `verify_admin_handle.py` - Database verification script
- `setup_test.py` - Prerequisites checker and setup helper
- `README.md` - This documentation

## Quick Start

### 1. Prerequisites Check
```bash
python setup_test.py
```

### 2. Start Services
```bash
# From the custom-storage-sql-pg directory
docker-compose up -d
```

### 3. Wait for Services
```bash
# Check service status
docker-compose ps

# View Handle Server logs
docker-compose logs handle-server

# Wait for PostgreSQL to be ready
docker-compose logs postgres
```

### 4. Verify Admin Handle
```bash
# Verify the admin handle was created correctly during database initialization
python verify_admin_handle.py
```

### 5. Test Handle Server
```bash
# Test with curl (always use timeouts!)
curl --connect-timeout 10 --max-time 30 \
  http://localhost:8000/api/handles/TEST/ADMIN

# Access web admin interface
# http://localhost:8000/admin/
```

## Database Direct Access

### Connect to PostgreSQL
```bash
# Using Docker
docker-compose exec postgres psql -U handleuser -d handledb

# Using local psql (if installed)
psql -h localhost -p 5432 -U handleuser -d handledb
```

### Useful SQL Queries
```sql
-- List all handles
SELECT DISTINCT handle FROM handles ORDER BY handle;

-- Show handle values
SELECT handle, idx, type, data FROM handles 
WHERE handle = 'TEST/ADMIN' ORDER BY idx;

-- Count total handles
SELECT COUNT(DISTINCT handle) FROM handles;

-- Show naming authorities
SELECT * FROM nas;
```

## Admin Handle Structure

The `create_admin_handle.py` script creates:

1. **TEST/ADMIN** handle with three values:
   - Index 100: `HS_ADMIN` - Admin permissions
   - Index 300: `HS_PUBKEY` - Public key (placeholder)
   - Index 301: `HS_SECKEY` - Secret key for authentication

2. **TEST** prefix in naming authority table

## Configuration Details

### Handle Server Environment
- `STORAGE_TYPE=sql` - Use SQL storage backend
- `SQL_DRIVER=postgresql` - PostgreSQL driver
- `SQL_URL=jdbc:postgresql://postgres:5432/handledb` - Database connection
- `STORAGE_NAMESPACE=TEST` - Handle prefix namespace
- `SERVER_ADMINS=300:111111111111:TEST/ADMIN` - Admin configuration

### PostgreSQL Database
- Database: `handledb`
- Username: `handleuser` 
- Password: `handlepass`
- Port: 5432

## Troubleshooting

### Services Not Starting
```bash
# Check Docker status
docker-compose ps

# View detailed logs
docker-compose logs

# Restart services
docker-compose restart
```

### Database Connection Issues
```bash
# Test PostgreSQL connectivity
docker-compose exec postgres pg_isready -U handleuser

# Check if database exists
docker-compose exec postgres psql -U handleuser -l
```

### Handle Server Issues
```bash
# View Handle Server logs
docker-compose logs handle-server

# Check if server is responding
curl --connect-timeout 5 --max-time 10 http://localhost:8000/
```

### Admin Handle Not Working
```bash
# Check if handle exists in database
python create_admin_handle.py

# Verify database content
docker-compose exec postgres psql -U handleuser -d handledb \
  -c "SELECT handle, idx, type FROM handles WHERE handle = 'TEST/ADMIN';"
```

## Advanced Usage

### Adding More Handles
```python
# Example: Add a test handle directly to PostgreSQL
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, 
    database='handledb', user='handleuser', password='handlepass'
)
cursor = conn.cursor()

# Add URL handle value
cursor.execute("""
    INSERT INTO handles (handle, idx, type, data, ttl_type, ttl,
                       timestamp_created, timestamp_updated,
                       admin_read, admin_write, pub_read, pub_write)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", ('TEST/EXAMPLE', 1, b'URL', b'https://example.com',
      0, 86400, int(time.time() * 1000), int(time.time() * 1000),
      True, True, True, True))

conn.commit()
conn.close()
```

### Backup and Restore
```bash
# Backup database
docker-compose exec postgres pg_dump -U handleuser handledb > backup.sql

# Restore database
docker-compose exec -T postgres psql -U handleuser handledb < backup.sql
```

## Security Notes

- Default credentials are for development only
- Change PostgreSQL password in production
- Use proper SSL certificates for HTTPS
- Restrict database access in production environments
- The secret key in the example is a placeholder - generate proper keys for production

## Comparison with Berkeley DB Setup

| Feature | PostgreSQL | Berkeley DB |
|---------|------------|-------------|
| Database Access | Direct SQL | Java Edition only |
| Admin Bootstrap | Python script | Batch tools + GHR |
| GHR Dependency | Independent | Required |
| Backup/Restore | Standard SQL | Specialized tools |
| Monitoring | SQL queries | Limited |
| Scalability | Full PostgreSQL | Single instance |
