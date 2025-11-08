# 🚀 Service Management Commands

## Start Service (with logs in terminal)

```bash
bash start.sh
```

**Output:**
```
🚀 Starting HMS Terminology Service...
INFO:     Will watch for changes in these directories: ['/path/to/data-machine']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Logs will appear in terminal** - Press `CTRL+C` to stop

---

## Stop Service

```bash
bash stop.sh
```

**Output:**
```
🛑 Stopping HMS Terminology Service...
✅ Service stopped
```

---

## Check Status

```bash
bash status.sh
```

**Output when running:**
```
🔍 Checking service status...
✅ Service is RUNNING

📊 Process info:
user  12346  0.5  0.3  uvicorn app.main:app

🌐 Access points:
   API Docs: http://localhost:8001/docs
   Root: http://localhost:8001/

🧪 Test:
   curl http://localhost:8001/
```

---

## Quick Commands

```bash
# Start (logs in terminal)
bash start.sh

# Stop (in another terminal)
bash stop.sh

# Check status
bash status.sh

# View logs (if running in background)
tail -f logs/app.log
```

---

## Access Points

- **API Documentation**: http://localhost:8001/docs
- **Root Endpoint**: http://localhost:8001/
- **Drug Search**: http://localhost:8001/api/v1/drugs/search?q=metformin
- **ICD-10 Search**: http://localhost:8001/api/v1/search/unified?query=diabetes

---

## Test API

```bash
# Test root
curl http://localhost:8001/

# Test drug search
curl "http://localhost:8001/api/v1/drugs/search?q=crocin"

# Test symptom search
curl "http://localhost:8001/api/v1/drugs/search?q=fever"

# Test ICD-10
curl "http://localhost:8001/api/v1/search/unified?query=diabetes"
```

---

## Troubleshooting

**Port already in use?**
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Or use stop script
bash stop.sh
```

**Service not starting?**
```bash
# Check Python
python --version

# Check dependencies
pip install -r requirements.txt

# Check database
psql -d hms_terminology -c "SELECT 1;"
```

**No logs appearing?**
```bash
# Check if service is running
bash status.sh

# View log files
tail -f logs/app.log
tail -f logs/error.log
```
