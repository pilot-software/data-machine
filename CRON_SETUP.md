# 🔄 Auto-Update Drug Database with Cron

## 📊 What Gets Updated

- ✅ **RxNorm data** - Latest generic drug mappings
- ✅ **Indian brands** - New brands and price updates
- ✅ **Indications** - Symptom/condition mappings

## 🚀 Quick Setup

### **Step 1: Download Expanded Data (200+ generics)**

```bash
python download_expanded_data.py
```

**Result:** 
- 60+ generics from RxNorm
- 30+ Indian brands
- Complete indications

### **Step 2: Load into Database**

```bash
python load_expanded_data.py
```

**Result:**
- Database updated with new drugs
- Existing drugs updated (prices, etc.)

### **Step 3: Setup Cron Job**

```bash
# Edit crontab
crontab -e

# Add this line (update weekly on Sunday 2 AM)
0 2 * * 0 /Users/samirkolhe/Desktop/New\ folder/data-machine/cron_update_drugs.sh

# Or update daily at 2 AM
0 2 * * * /Users/samirkolhe/Desktop/New\ folder/data-machine/cron_update_drugs.sh

# Or update monthly (1st of month)
0 2 1 * * /Users/samirkolhe/Desktop/New\ folder/data-machine/cron_update_drugs.sh
```

### **Step 4: Test Cron Script**

```bash
# Run manually to test
./cron_update_drugs.sh

# Check logs
tail -f logs/cron_update.log
```

## 📅 Recommended Update Frequency

| Data Source | Update Frequency | Cron Schedule |
|-------------|------------------|---------------|
| **RxNorm** | Weekly | `0 2 * * 0` (Sunday 2 AM) |
| **Indian Brands** | Monthly | `0 2 1 * *` (1st of month) |
| **Prices (NPPA)** | Quarterly | Manual download |

## 🎯 Cron Schedule Examples

```bash
# Every Sunday at 2 AM
0 2 * * 0 /path/to/cron_update_drugs.sh

# Every day at 2 AM
0 2 * * * /path/to/cron_update_drugs.sh

# First day of every month at 2 AM
0 2 1 * * /path/to/cron_update_drugs.sh

# Every 6 hours
0 */6 * * * /path/to/cron_update_drugs.sh
```

## 📊 Current Data Status

After running expanded download:

```
✅ Generic Ingredients: 60+
✅ Brand Drugs: 130+
✅ RxNorm Mapping: Complete
✅ Symptom Search: Enhanced
```

## 🔍 Monitor Updates

### **Check Last Update**

```bash
# View cron logs
tail -20 logs/cron_update.log

# Check database stats
psql -d hms_terminology -c "
SELECT 
    'Generics' as type, COUNT(*) as count 
FROM generic_ingredients
UNION ALL
SELECT 
    'Brands', COUNT(*) 
FROM indian_brand_drugs;
"
```

### **Verify Cron is Running**

```bash
# List active cron jobs
crontab -l

# Check cron service (macOS)
sudo launchctl list | grep cron

# Check cron logs (Linux)
grep CRON /var/log/syslog
```

## 🚨 Troubleshooting

### **Cron not running?**

```bash
# Check cron service
sudo launchctl list | grep cron

# Restart cron (macOS)
sudo launchctl stop com.vix.cron
sudo launchctl start com.vix.cron

# Check permissions
ls -la cron_update_drugs.sh
# Should show: -rwxr-xr-x
```

### **Script fails?**

```bash
# Run manually to see errors
./cron_update_drugs.sh

# Check logs
cat logs/cron_update.log

# Test database connection
psql -d hms_terminology -c "SELECT 1;"
```

### **No new data?**

```bash
# RxNorm API might be down
curl "https://rxnav.nlm.nih.gov/REST/rxcui.json?name=metformin"

# Check internet connection
ping rxnav.nlm.nih.gov
```

## 📈 Scaling to More Data

### **Option 1: Expand Generic List**

Edit `download_expanded_data.py`:

```python
INDIAN_GENERICS = [
    # Add 100+ more generics here
    "Pregabalin", "Gabapentin", "Duloxetine", ...
]
```

### **Option 2: Add NPPA Price Updates**

```bash
# Download NPPA price list quarterly
wget https://www.nppaindia.nic.in/ceiling-price/list.xlsx

# Convert and load
python load_nppa_prices.py
```

### **Option 3: Integrate MIMS API**

```python
# Add to cron_update_drugs.sh
python sync_mims_api.py
```

## 🎯 Production Setup

### **For Production Server:**

```bash
# 1. Setup on server
ssh user@server
cd /opt/hms-terminology

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup cron
crontab -e
0 2 * * 0 /opt/hms-terminology/cron_update_drugs.sh

# 4. Setup monitoring
# Add alerting if update fails
```

### **With Docker:**

```dockerfile
# Add to Dockerfile
COPY cron_update_drugs.sh /app/
RUN chmod +x /app/cron_update_drugs.sh

# Add cron to container
RUN apt-get install -y cron
RUN echo "0 2 * * 0 /app/cron_update_drugs.sh" | crontab -
```

## ✅ Verification Checklist

After setup:

- [ ] Cron job added to crontab
- [ ] Script is executable (`chmod +x`)
- [ ] Logs directory exists
- [ ] Database connection works
- [ ] RxNorm API accessible
- [ ] Test run successful
- [ ] Monitoring setup

## 📊 Expected Results

**After first run:**
```
✅ 60+ generic drugs
✅ 130+ Indian brands
✅ Complete RxNorm mapping
✅ Symptom search working
```

**After weekly updates:**
```
✅ New generics added automatically
✅ Prices updated
✅ New brands discovered
✅ Database stays current
```

## 🎯 Next Steps

1. ✅ Run expanded download now
2. ✅ Setup weekly cron
3. ✅ Monitor first update
4. 🔄 Scale to MIMS when ready

**Your database will auto-update every week!** 🔄
