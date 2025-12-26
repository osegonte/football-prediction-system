# ⚽ Football Data Collector

Complete football data collection system for ML-based betting analysis.

---

## 🚀 Quick Start

### **Setup (One Time)**

```bash
# 1. Clone & setup
git clone <your-repo-url>
cd football-prediction-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup database
python setup_database.py

# 3. Configure .env
cp .env.example .env
nano .env  # Add your credentials

# 4. Test (30 minutes)
python test_collector.py

# 5. Run full collection (2-3 days)
python collector.py
```

---

## 📊 What It Does

**Single `collector.py` script collects:**
1. ✅ All fixtures (Jan 1, 2025 → Today)
2. ✅ Team baseline (10 matches before 2025)
3. ✅ All 2025 team matches
4. ✅ Match statistics (detailed stats)
5. ✅ Player statistics (individual performance)

**Automatically resumes if interrupted!**

---

## 🧪 Testing

```bash
# Quick 30-min test on random day
python test_collector.py

# Check CSV outputs
ls -lh data/test/
```

---

## 📱 Monitoring

```bash
# Start monitor bot
python telegram_monitor.py

# Telegram commands:
/status - Quick overview
/progress - Visual progress bars
/teams - Team details
/stats - Full statistics
```

---

## 🗄️ Database

Schema: `database/schema.sql`  
Setup: `python setup_database.py`

**Tables:** fixtures, team_matches, match_statistics, player_statistics

---

## 🔧 Configuration

`.env` file:
```env
DB_NAME=football_data
DB_USER=osegonte
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## ✅ Summary

**3 Core Files:**
1. `collector.py` - Main collector
2. `test_collector.py` - 30-min test
3. `telegram_monitor.py` - Live monitoring

**Run test first:** `python test_collector.py` 🚀