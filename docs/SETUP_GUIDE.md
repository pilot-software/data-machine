# 🚀 HMS Terminology Service - Setup Guide

## Prerequisites

- macOS/Linux
- Python 3.9+
- PostgreSQL 14+
- Git

---

## 📋 Quick Setup (5 minutes)

### 1. Clone Repository
```bash
git clone <repository-url>
cd data-machine
```

### 2. Run Setup Script
```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Setup PostgreSQL database
- Create database schema

### 3. Start Service
```bash
./start.sh
```

### 4. Verify
```bash
# Check health
curl http://localhost:8001/api/v1/health

# View API docs
open http://localhost:8001/docs
```

---

## 🔧 Manual Setup (if scripts fail)

### 1. Install Dependencies

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Install Redis (optional)
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib python3-pip python3-venv
sudo systemctl start postgresql
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Database
```bash
# Create database
createdb hms_terminology

# Or using psql
psql -d postgres -c "CREATE DATABASE hms_terminology;"

# Setup schema
python scripts/setup_full_db.py
```

### 4. Configure Environment
```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://$(whoami)@localhost:5432/hms_terminology
APP_NAME=HMS Terminology Service
APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=8001
DEBUG=true
LOG_LEVEL=INFO
EOF
```

### 5. Load Sample Data (Optional)
```bash
# Load drug data
python scripts/etl/load_sample_data.py

# Load AB-HBP data (if available)
python scripts/etl/load_abhbp_data.py
```

### 6. Start Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

---

## 📊 Database Setup Details

### Required Tables
- `icd10_codes` - ICD-10 medical codes
- `icd11_codes` - ICD-11 medical codes
- `indian_brand_drugs` - Indian drug brands
- `generic_ingredients` - Generic drug ingredients
- `drug_interactions` - Drug interaction data
- `abhbp_procedures` - Ayushman Bharat procedures

### Auto-created by setup script
All tables are created automatically when you run `./setup.sh` or `python scripts/setup_full_db.py`

---

## 🧪 Testing

### Run Tests
```bash
# Quick API test
./test_api.sh

# Unit tests
pytest tests/test_api_consolidated.py -v

# Specific test
pytest tests/test_api_consolidated.py::test_health -v
```

---

## 📚 API Endpoints

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health

### ICD Search
- `GET /api/v1/icd10/search?q=diabetes` - Search ICD codes
- `GET /api/v1/icd10/{code}` - Get code details
- `GET /api/v1/icd10/chapters` - List chapters

### Clinical (Doctor-friendly)
- `GET /api/v1/clinical/search?q=headache` - Clinical search
- `GET /api/v1/clinical/common` - Common conditions

### Drugs
- `GET /api/v1/drugs/search?q=metformin` - Search drugs
- `GET /api/v1/drugs/{id}` - Drug details
- `POST /api/v1/drugs/interactions` - Check interactions

### AB-HBP
- `GET /api/v1/abhbp/search?q=surgery` - Search procedures
- `GET /api/v1/abhbp/{code}` - Procedure details

**Full docs**: http://localhost:8001/docs

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8002
```

### Database Connection Error
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@14

# Check connection
psql -d hms_terminology -c "SELECT 1;"
```

### Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### WHO API Timeout
```bash
# The setup script has 45s timeout for WHO API
# If it fails, it will skip and continue
# You can load data later with:
python scripts/etl/download_icd10_complete.py
```

---

## 📁 Project Structure

```
data-machine/
├── app/
│   ├── api/
│   │   ├── v1_consolidated.py    # Main API endpoints
│   │   └── clinical_search.py    # Clinical endpoints
│   ├── db/                        # Database models
│   ├── services/                  # Business logic
│   └── main.py                    # FastAPI app
├── scripts/
│   ├── etl/                       # Data loading scripts
│   ├── setup_full_db.py          # Database setup
│   └── setup_drug_db.sql         # Drug schema
├── tests/
│   └── test_api_consolidated.py  # API tests
├── docs/                          # Documentation
├── setup.sh                       # Setup script
├── start.sh                       # Start script
├── test_api.sh                    # Test script
└── requirements.txt               # Python dependencies
```

---

## 🔐 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user@localhost:5432/hms_terminology` | PostgreSQL connection |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8001` | Server port |
| `DEBUG` | `true` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REDIS_HOST` | `localhost` | Redis host (optional) |
| `REDIS_PORT` | `6379` | Redis port (optional) |

---

## 🚀 Production Deployment

### 1. Update Environment
```bash
# Set production values in .env
DEBUG=false
LOG_LEVEL=WARNING
```

### 2. Use Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### 3. Setup Nginx (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📞 Support

- **Documentation**: `docs/API_ENDPOINTS_V1.md`
- **Quick Reference**: `API_QUICK_REFERENCE.md`
- **API Docs**: http://localhost:8001/docs

---

## ✅ Checklist for New Developers

- [ ] Clone repository
- [ ] Run `./setup.sh`
- [ ] Run `./start.sh`
- [ ] Open http://localhost:8001/docs
- [ ] Run `./test_api.sh`
- [ ] Read `API_QUICK_REFERENCE.md`
- [ ] Try sample API calls
- [ ] Run unit tests: `pytest tests/ -v`

---

**Built for Indian Healthcare** 🇮🇳
