# 🚀 Quick Deployment Guide

## After Installation

Once `install.sh` completes, the server is already running!

### Daily Commands

```bash
./start.sh    # Start server
./stop.sh     # Stop server
./restart.sh  # Restart server
./status.sh   # Check status
```

---

## Fresh Machine Setup (Single Command)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd data-machine

# 2. Download data files (one-time)
./download_data.sh

# 3. Install & start
./install.sh
```

That's it! The script will:
1. ✅ Check prerequisites (Python3, PostgreSQL)
2. ✅ Install dependencies
3. ✅ Setup environment (.env)
4. ✅ Create database
5. ✅ Load ICD-10/11 codes
6. ✅ Load SNOMED drugs (89K+ brands)
7. ✅ Load RF2 extended data (classifications)
8. ✅ Start server on port 8001

---

## Prerequisites

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip postgresql postgresql-contrib
```

### macOS
```bash
brew install python3 postgresql
brew services start postgresql
```

### CentOS/RHEL
```bash
sudo yum install -y python3 python3-pip postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
```

---

## Required Files

Place these in project root before running `install.sh`:

1. **CommonDrugCodesForIndia_FlatFilePackage/** (Required)
   - Download from: https://www.nrces.in/standards/snomed-ct
   - Contains: BrandMaster.txt, GenericMaster.txt, etc.

2. **SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z/** (Optional)
   - For drug classifications and hierarchies
   - Download from: https://www.nrces.in/standards/snomed-ct

3. **.env** (Auto-created from .env.example)
   ```bash
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=medical_library
   DB_USER=your_username
   DB_PASSWORD=your_password
   XAI_API_KEY=your_grok_api_key  # Optional for AI features
   ```

---

## Manual Commands (If Needed)

### Start Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Stop Server
```bash
pkill -f "uvicorn app.main:app"
```

### Check Status
```bash
curl http://localhost:8001/api/v1/health
```

### View Logs
```bash
tail -f logs/server.log
```

---

## Test Installation

```bash
# Health check
curl http://localhost:8001/api/v1/health

# Search ICD codes
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/icd/search?q=diabetes"

# Search drugs
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/search?q=paracetamol"

# Get all antibiotics
curl -H "X-API-Key: dev-key-123" \
  "http://localhost:8001/api/v1/snomed/extended/antibiotics"

# AI diagnosis
curl -X POST -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fever","cough"],"patient_age":35}' \
  "http://localhost:8001/api/v1/clinical-ai/diagnose"
```

---

## Production Deployment

### Using systemd (Recommended)

Create `/etc/systemd/system/hms-api.service`:

```ini
[Unit]
Description=HMS Terminology Service
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/data-machine
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hms-api
sudo systemctl start hms-api
sudo systemctl status hms-api
```

### Using Docker

```bash
# Build
docker build -t hms-api .

# Run
docker run -d -p 8001:8001 \
  -e DB_HOST=host.docker.internal \
  -e DB_NAME=medical_library \
  --name hms-api hms-api
```

---

## Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check credentials in .env
cat .env

# Test connection
psql -U your_user -d medical_library -c "SELECT 1;"
```

### Server Won't Start
```bash
# Check logs
tail -f logs/server.log

# Check port availability
lsof -i :8001

# Kill existing process
pkill -f "uvicorn app.main:app"
```

### Missing Data
```bash
# Re-run data loading
python3 scripts/etl/load_snomed_data.py
python3 scripts/etl/load_snomed_rf2_extended.py
```

---

## Performance Tuning

### PostgreSQL
Edit `/etc/postgresql/*/main/postgresql.conf`:
```ini
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

### Uvicorn Workers
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8001
```

---

## Support

- **Documentation**: http://localhost:8001/docs
- **Logs**: `logs/server.log`, `logs/snomed_etl.log`
- **Database Stats**: `psql -U user -d medical_library -c "SELECT COUNT(*) FROM snomed_brands;"`
