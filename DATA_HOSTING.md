# 📦 Data Files Hosting Guide

## Problem
Data files are too large for Git (1.5GB total):
- `CommonDrugCodesForIndia_FlatFilePackage/` - 500MB
- `SnomedCT_IndiaDrugExtensionRF2_*/` - 1GB

## Solutions

### Option 1: Official Source (Recommended)
**Everyone downloads from NRCES**

```bash
./download_data.sh
# Follow prompts to download from https://www.nrces.in/standards/snomed-ct
```

**Pros**: Always latest data, official source
**Cons**: Requires registration, manual download

---

### Option 2: Team Shared Drive (Best for Teams)
**Host on Google Drive/Dropbox/OneDrive**

#### Setup (One-time by admin):
```bash
# 1. Zip the data
zip -r snomed-data.zip \
  CommonDrugCodesForIndia_FlatFilePackage/ \
  SnomedCT_IndiaDrugExtensionRF2_*/

# 2. Upload to Google Drive/Dropbox
# 3. Get shareable link
# 4. Share with team
```

#### Usage (Team members):
```bash
# Download from shared link
wget "https://drive.google.com/uc?id=YOUR_FILE_ID" -O snomed-data.zip

# Extract
unzip snomed-data.zip

# Install
./install.sh
```

**Pros**: Fast, no registration needed
**Cons**: Need to maintain/update

---

### Option 3: Private Package Registry
**Host on Artifactory/Nexus/S3**

```bash
# Download from private registry
aws s3 cp s3://your-bucket/snomed-data.zip .
unzip snomed-data.zip
./install.sh
```

**Pros**: Enterprise-grade, version control
**Cons**: Requires infrastructure

---

### Option 4: Docker Image (All-in-One)
**Bundle data with Docker image**

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
# Data files included in image
RUN ./install.sh
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

```bash
# Build once (includes data)
docker build -t hms-api:latest .

# Deploy anywhere
docker run -p 8001:8001 hms-api:latest
```

**Pros**: One-step deployment, no separate download
**Cons**: Large image (~2GB)

---

## Recommended Approach

### For Small Teams (< 10 people)
**Use Google Drive/Dropbox**

1. Admin zips data files
2. Upload to shared drive
3. Share link in README
4. Team downloads once

### For Large Teams/Enterprise
**Use Private S3/Artifactory**

1. Upload to S3 bucket
2. Create download script with credentials
3. Automate in CI/CD

### For Public/Open Source
**Document official source**

1. Point to NRCES website
2. Provide `download_data.sh` script
3. Users download themselves

---

## Update README

Add this to your README.md:

```markdown
## Data Files Setup

Data files are not included in Git. Download them:

### Option 1: Automated (Recommended)
\`\`\`bash
./download_data.sh
\`\`\`

### Option 2: Manual Download
1. Visit: https://www.nrces.in/standards/snomed-ct
2. Download:
   - CommonDrugCodesForIndia_FlatFilePackage.zip
   - SnomedCT_IndiaDrugExtensionRF2_*.zip
3. Extract to project root
4. Run: ./install.sh

### Option 3: Team Shared Drive (If Available)
\`\`\`bash
# Contact admin for shared drive link
wget <shared-link> -O snomed-data.zip
unzip snomed-data.zip
./install.sh
\`\`\`
```

---

## Quick Setup Script (With Auto-Download)

Create `quick-setup.sh`:

```bash
#!/bin/bash
# One-command setup with data download

# Clone repo
git clone <your-repo>
cd data-machine

# Download data (if you have direct URL)
wget "YOUR_SHARED_DRIVE_URL" -O snomed-data.zip
unzip -q snomed-data.zip
rm snomed-data.zip

# Install
./install.sh

echo "✅ Setup complete! Server running on http://localhost:8001"
```

Share this with your team!
