# Healthcare Email Scraper - Complete Guide

## 🎯 **Purpose**

The Healthcare Email Scraper extracts contact email addresses from healthcare practice websites, focusing on secretary and management emails for practices marked with `zuweisung = 1` in the CRM system.

## 📊 **Data Source**

**Input**: `_TMP/entries.csv` - Healthcare practices from CRM system
- **Filters**: Only processes entries where `zuweisung = 1` 
- **URL Source**: Extracts websites from JSON `linkUrl` field
- **Target**: German-speaking Swiss healthcare practices

## 🔍 **Email Extraction Strategy**

### **Multiple Detection Methods**
1. **Mailto Links** (Most Reliable)
   - Extracts from `<a href="mailto:...">` elements
   - Handles query parameters and cleaning
   
2. **Text Pattern Matching**
   - Regex pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}`
   - Scans entire page content
   
3. **Targeted Element Search**
   - Contact sections, footer elements
   - German terms: kontakt, sekretariat, verwaltung

### **Email Categorization**

**Priority Emails** (Secretary/Management):
- Prefixes: `info`, `kontakt`, `sekretariat`, `verwaltung`, `anmeldung`, `termine`, `contact`, `secretary`, `admin`, `office`, `praxis`
- Examples: `info@praxis.ch`, `sekretariat@klinik.ch`

**General Practice Emails**:
- Contains: `praxis`, `klinik`, `arzt`
- Examples: `praxis@domain.ch`, `klinik.name@hin.ch`

**Other Emails**:
- All remaining valid email addresses

## 🚀 **Usage**

### **Quick Start**
```bash
# Navigate to scrapers directory
cd _scrapers

# Activate virtual environment
source venv/bin/activate

# Run email scraper via manager (recommended)
python scraper_manager.py run email-scraper

# Or run directly
python email_scraper.py
```

### **Advanced Options**
```bash
# Force run (ignore existing data)
python scraper_manager.py run email-scraper --force

# Check status
python scraper_manager.py list | grep -A 10 EMAIL-SCRAPER

# View statistics
python scraper_manager.py stats
```

## 📋 **Output Format**

### **CSV Fields**
- `id` - Original entry ID from CRM
- `title` - Practice name
- `url` - Website URL scraped
- `emails` - All found emails (semicolon separated)
- `priority_emails` - Secretary/management emails
- `general_emails` - General practice emails  
- `other_emails` - Other email addresses
- `total_emails_found` - Count of emails found
- `scraping_status` - success/no_emails/failed/no_url
- `error` - Error message if failed
- `scraped_at` - Timestamp

### **Example Output**
```csv
id,title,url,emails,priority_emails,general_emails,other_emails,total_emails_found,scraping_status,error,scraped_at
312807,Augenarzt Sarnen,https://augenarzt-obwalden.ch/,info@augenarzt-obwalden.ch,info@augenarzt-obwalden.ch,,,1,success,,2025-09-10T12:31:06
```

## 🔧 **Technical Features**

### **Robust Error Handling**
- Handles network timeouts and connection errors
- Graceful handling of invalid URLs
- Continues processing even if individual sites fail
- Progress saving every 10 entries

### **Rate Limiting**
- Random delays between requests (1-3 seconds)
- Respects website resources
- Extended timeout for complex sites

### **Swiss Healthcare Optimization**
- Recognizes HIN.ch email system (Swiss healthcare network)
- German language term recognition
- Swiss medical practice URL patterns

### **Email Validation**
- Format validation using regex
- Duplicate removal
- Length and character validation
- Cleanup of malformed addresses

## 📈 **Performance & Scale**

### **Expected Performance**
- **Processing Rate**: ~3-5 websites per minute (with rate limiting)
- **Success Rate**: ~60-80% (depending on website structure)
- **Timeout**: 2 hours maximum runtime
- **Memory Usage**: Low (processes one site at a time)

### **For Large Datasets**
- Automatic progress saving
- Resumable if interrupted
- Progress logging every 10 entries
- Memory efficient (no bulk loading)

## 🛡️ **Error Handling & Recovery**

### **Common Scenarios**
- **No URL**: Entry marked as `no_url`
- **Site Down**: Marked as `failed` with error message
- **No Emails Found**: Marked as `no_emails` (not an error)
- **Invalid JSON**: URL extraction fails, continues processing

### **Recovery Options**
- Progress files allow resumption
- Failed entries can be re-run individually
- Error details logged for debugging

## 🎛️ **Configuration**

### **Customizable Elements**
```python
# In email_scraper.py
priority_prefixes = ['info', 'kontakt', 'sekretariat', 'verwaltung', ...]
priority_terms = ['sekretariat', 'secretary', 'verwaltung', ...]
```

### **Rate Limiting**
```python
delay = random.uniform(1.0, 3.0)  # Adjust as needed
timeout = 10  # Request timeout
```

## 📊 **Integration with CRM System**

### **Data Flow**
1. **Input**: CRM entries CSV with `zuweisung = 1`
2. **Processing**: Extract emails from practice websites
3. **Output**: Enriched CSV with email addresses
4. **Integration**: Import back to CRM system for marketing campaigns

### **Use Cases**
- **MediTransfer Marketing**: Contact practices for patient transfer services
- **Partnership Development**: Reach out to practice management
- **Service Promotion**: Direct communication with decision makers

## ⚡ **Quick Commands**

```bash
# Check how many entries will be processed
python3 -c "
import csv
with open('_TMP/entries.csv', 'r') as f:
    count = sum(1 for row in csv.DictReader(f) if row.get('zuweisung') == '1')
    print(f'{count} entries marked for email scraping')
"

# Run on subset for testing
head -50 _TMP/entries.csv > _TMP/test_entries.csv
# Edit email_scraper.py to use test file temporarily

# Monitor progress during run
tail -f email_scraping_progress.csv

# View results after completion
python3 -c "
import pandas as pd
df = pd.read_csv('scraped_emails.csv')
print(f'Total processed: {len(df)}')
print(f'Successful: {len(df[df.scraping_status == \"success\"])}')
print(f'Total emails: {df.total_emails_found.sum()}')
"
```

## 🚨 **Important Notes**

### **Compliance**
- Respects website robots.txt (implement if needed)
- Rate limiting to avoid overloading servers
- Use collected emails responsibly for legitimate business purposes

### **Data Quality**
- Email validation is basic - verify important addresses manually
- Some websites may use contact forms instead of direct emails
- Dynamic content may not be captured (JavaScript-heavy sites)

### **Maintenance**
- Website structures change - may need pattern updates
- HIN.ch system changes could affect Swiss healthcare emails
- Regular testing recommended on sample data

---

**The Healthcare Email Scraper is now fully integrated with the unified scraper system and ready for production use.**