# 🔐 Authentication Guide

## Overview

Simple API Key authentication for production use.

---

## 🚀 Quick Start

### 1. Enable Authentication

Edit `.env`:
```bash
AUTH_ENABLED=true
API_KEYS=your-secret-key-1,your-secret-key-2,your-secret-key-3
```

### 2. Use API Key

**Header**:
```
X-API-Key: your-secret-key-1
```

**Example**:
```bash
curl -H "X-API-Key: dev-key-123" http://localhost:8001/api/v1/protected/stats
```

---

## 📋 Endpoints

### Public (No Auth Required)
- `GET /` - Root
- `GET /api/v1/health` - Basic health
- `GET /docs` - Swagger docs

### Protected (Auth Required)
- `GET /api/v1/protected/stats` - Database statistics
- `GET /api/v1/protected/health/detailed` - Detailed health

### Optional Auth (Configurable)
- All `/api/v1/*` endpoints can be protected by adding `dependencies=[Depends(verify_api_key)]`

---

## 🔑 Managing API Keys

### Add New Key
Edit `.env`:
```bash
API_KEYS=key1,key2,new-key-3
```

### Generate Secure Key
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### Revoke Key
Remove from `.env` and restart server.

---

## 🛡️ Security Best Practices

### Development
```bash
AUTH_ENABLED=false
API_KEYS=dev-key-123
```

### Production
```bash
AUTH_ENABLED=true
API_KEYS=prod-key-xyz-secure-random-string
```

**Never commit production keys to git!**

---

## 🧪 Testing

### Without Auth (Public)
```bash
curl http://localhost:8001/api/v1/health
```

### With Auth (Protected)
```bash
# Valid key
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8001/api/v1/protected/stats

# Invalid key (403)
curl -H "X-API-Key: wrong-key" \
  http://localhost:8001/api/v1/protected/stats

# Missing key (401)
curl http://localhost:8001/api/v1/protected/stats
```

---

## 📊 Response Codes

| Code | Meaning | Reason |
|------|---------|--------|
| 200 | Success | Valid API key |
| 401 | Unauthorized | Missing API key |
| 403 | Forbidden | Invalid API key |

---

## 🔧 Advanced: Protect All Endpoints

Edit `app/main.py`:

```python
from app.middleware.auth import verify_api_key
from fastapi import Depends

# Protect all v1 endpoints
app.include_router(
    v1_router,
    dependencies=[Depends(verify_api_key)]
)
```

---

## 🌐 Frontend Integration

### JavaScript
```javascript
fetch('http://localhost:8001/api/v1/protected/stats', {
  headers: {
    'X-API-Key': 'your-api-key'
  }
})
```

### Python
```python
import requests

headers = {'X-API-Key': 'your-api-key'}
response = requests.get(
    'http://localhost:8001/api/v1/protected/stats',
    headers=headers
)
```

### cURL
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8001/api/v1/protected/stats
```

---

## 🔄 Migration Plan

### Phase 1: Add Auth (Current)
- ✅ Auth middleware created
- ✅ Protected endpoints added
- ✅ Public endpoints remain open

### Phase 2: Gradual Protection
- Move sensitive endpoints to protected
- Keep search endpoints public
- Monitor usage

### Phase 3: Full Protection
- Protect all endpoints
- Issue keys to clients
- Monitor and revoke as needed

---

## 📝 API Key Format

**Recommended**:
- Length: 32+ characters
- Format: `{env}-{purpose}-{random}`
- Example: `prod-frontend-a8f3k2j9d8s7f6g5h4j3k2l1`

**Bad**:
- ❌ `123456`
- ❌ `api-key`
- ❌ `password`

**Good**:
- ✅ `prod-web-8kJ3nM9pL2qR5tY7wX4vZ6bN1cM8`
- ✅ `dev-mobile-xY9kL3mN7pQ2rT5wV8zB4cD6fG1h`

---

## 🚨 Security Notes

1. **HTTPS Only**: Use HTTPS in production
2. **Rotate Keys**: Change keys every 90 days
3. **Monitor Usage**: Log all API key usage
4. **Rate Limiting**: Already implemented
5. **IP Whitelist**: Consider adding for production

---

## ✅ Current Status

- ✅ Auth middleware created
- ✅ Protected endpoints added
- ✅ Public endpoints working
- ✅ Documentation complete
- ⚠️ AUTH_ENABLED=false (for development)

**To enable**: Set `AUTH_ENABLED=true` in `.env`
