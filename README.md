# Gmail AI Classifier 📧

Automatically categorize Gmail emails into 15 categories using free Groq AI (meta-llama/llama-prompt-guard-2-86m).

## Categories
- **Job Offers** - Interview invites, offer letters, recruiter messages
- **Spam** - Scams, phishing, unwanted marketing
- **OTP/Verification** - 2FA codes, login alerts, security codes
- **Payments/Transactions** - UPI, bank transfers, receipts
- **Credit Card Bills** - Statements, due reminders
- **Bank Statements** - Monthly account statements
- **Subscriptions** - SaaS renewals, membership fees
- **Social/Notifications** - Social media alerts
- **Newsletters** - Digest emails, mailing lists
- **Promotions** - Sales, discounts, coupons
- **Travel/Bookings** - Flights, hotels, tickets
- **Shopping/Orders** - Order confirmations, shipping
- **Government/Official** - Tax, Aadhaar, passport
- **Health/Medical** - Reports, appointments, insurance
- **Education/Learning** - Courses, certificates, exams

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Gmail API credentials (`credentials.json`) from [Google Cloud Console](https://console.cloud.google.com/)
- Free Groq API key from [console.groq.com](https://console.groq.com/keys)
- Free Supabase project from [supabase.com](https://supabase.com)

### 2. Local Setup
```bash
# Clone & install
git clone <your-repo>
cd gmail-ai-agent
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Run Supabase schema (in Supabase SQL Editor)
# See supabase_schema.sql

# Run locally
python gmail_ai_agent.py --unread
# Or web UI
streamlit run app.py
```

### 3. Deploy to Streamlit Cloud (Free)
1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Connect GitHub repo, branch `main`, file `app.py`
4. Add **Secrets** in Streamlit dashboard:
```toml
GROQ_API_KEY = "gsk_..."
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
GOOGLE_CREDENTIALS_JSON = """{ "installed": { ... } }"""
```
5. Deploy → Get public URL
6. On phone: Open URL → "Add to Home Screen" → Native app experience

## Project Structure
```
gmail-ai-agent/
├── gmail_ai_agent.py    # Core CLI agent
├── app.py               # Streamlit web/mobile app
├── supabase_db.py       # Supabase PostgreSQL layer
├── supabase_schema.sql  # Database schema
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
└── credentials.json     # Gmail OAuth (NOT in git)
```

## Usage

### CLI
```bash
# Process unread emails only
python gmail_ai_agent.py --unread

# Process all emails (reprocess)
python gmail_ai_agent.py --all --reprocess

# Include spam/trash folders
python gmail_ai_agent.py --spam
```

### Web App
Open `http://localhost:8501` (local) or Streamlit Cloud URL:
- **Dashboard** - Stats, charts
- **Emails** - Browse by category
- **Process** - One-click categorization
- **Analytics** - Distribution, confidence

## Privacy
- Only **Subject + Sender** sent to AI (never email body)
- Data stored in your Supabase project (you own it)
- Gmail token stored locally (`token.pickle`)

## Free Tier Limits
| Service | Free Limit |
|---------|-----------|
| Groq (meta-llama/llama-prompt-guard-2-86m) | 14,400 req/day |
| Supabase PostgreSQL | 500 MB |
| Streamlit Cloud | Unlimited public apps |
| Gmail API | 250 quota/user/sec |

## License
MIT