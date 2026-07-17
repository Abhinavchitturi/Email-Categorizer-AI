"""
Gmail AI Agent - Categorizes emails using Groq AI (free tier)
Only uses Subject + Sender for categorization (privacy-focused)
Uses Supabase (PostgreSQL) for cloud database
"""

import os
import json
import pickle
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from groq import Groq

from supabase_db import SupabaseDB, Email

load_dotenv()

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify'
]

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'

CATEGORIES = [
    "Job Offers",
    "Spam",
    "OTP/Verification",
    "Payments/Transactions",
    "Credit Card Bills",
    "Bank Statements",
    "Subscriptions",
    "Social/Notifications",
    "Newsletters",
    "Promotions",
    "Travel/Bookings",
    "Shopping/Orders",
    "Government/Official",
    "Health/Medical",
    "Education/Learning",
    "Other"
]

CATEGORY_DESCRIPTIONS = {
    "Job Offers": "Job offers, interview invites, recruiter messages, application updates, offer letters",
    "Spam": "Spam, scams, phishing, unsolicited marketing, suspicious emails",
    "OTP/Verification": "OTP codes, verification codes, 2FA codes, login alerts, security codes",
    "Payments/Transactions": "Payment confirmations, transaction alerts, UPI payments, transfers, receipts",
    "Credit Card Bills": "Credit card statements, bill due reminders, payment due, statement ready",
    "Bank Statements": "Bank account statements, monthly statements, account summaries (subject only, no body)",
    "Subscriptions": "Subscription renewals, membership fees, SaaS bills, recurring payments",
    "Social/Notifications": "Social media notifications, friend requests, messages, likes, comments",
    "Newsletters": "Newsletters, digest emails, weekly/monthly updates from subscribed sources",
    "Promotions": "Marketing promotions, sales, discounts, coupon codes, promotional offers",
    "Travel/Bookings": "Flight/train/hotel bookings, travel confirmations, itinerary, tickets",
    "Shopping/Orders": "Order confirmations, shipping updates, delivery notifications, returns",
    "Government/Official": "Government communications, tax notices, official documents, Aadhaar, PAN",
    "Health/Medical": "Medical reports, appointments, pharmacy, lab results, insurance claims",
    "Education/Learning": "Course updates, certificates, learning platforms, exam results",
    "Other": "Anything that doesn't fit above categories"
}

from supabase_db import SupabaseDB, Email

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GmailClient:
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        # Use refresh token from env (works on Streamlit Cloud)
        # Fall back to local token.pickle for local development
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        
        if client_id and client_secret and refresh_token:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=SCOPES
            )
        elif os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as f:
                creds = pickle.load(f)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
        else:
            raise RuntimeError(
                "No Google credentials found. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "
                "GOOGLE_REFRESH_TOKEN in env (Streamlit Cloud) or run locally to create token.pickle"
            )
        
        self.service = build('gmail', 'v1', credentials=creds)
        profile = self.service.users().getProfile(userId='me').execute()
        print(f"Connected to: {profile['emailAddress']}")
    
    def fetch_emails(self, query: str = '', max_results: int = 100, 
                     include_spam_trash: bool = False) -> List[Dict]:
        if include_spam_trash:
            query = f"{query} in:anywhere".strip()
        
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            detail = self.service.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['Subject', 'From', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in detail['payload'].get('headers', [])}
            emails.append({
                'message_id': msg['id'],
                'sender': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'snippet': detail.get('snippet', ''),
                'date': headers.get('Date', '')
            })
        
        return emails

class GroqClassifier:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.enabled = bool(self.api_key and self.api_key != 'your_groq_api_key_here')
    
    def build_prompt(self, sender: str, subject: str) -> str:
        cat_list = "\n".join([f'- {c}: {CATEGORY_DESCRIPTIONS[c]}' for c in CATEGORIES])
        
        return f"""Categorize this email using ONLY the sender and subject (privacy: no body content).

Sender: {sender}
Subject: {subject}

Categories:
{cat_list}

Return ONLY valid JSON:
{{"category": "exact_category_name", "confidence": 0.0-1.0, "reasoning": "brief reason"}}

Rules:
- Use EXACT category names from list above
- Only use sender/subject for decision
- For bank statements: categorize as "Bank Statements" from subject only
- Credit card bills = "Credit Card Bills"
- OTP/verification codes = "OTP/Verification"
- Job offers/interviews = "Job Offers"
- Spam/scam/phishing = "Spam"
- If unsure, use "Other" with low confidence"""
    
    def classify(self, sender: str, subject: str) -> Tuple[str, float, str]:
        if not self.enabled or not self.client:
            return self._rule_based(sender, subject)
        
        prompt = self.build_prompt(sender, subject)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.1,
                max_tokens=200,
                response_format={'type': 'json_object'}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            category = parsed.get('category', 'Other')
            confidence = float(parsed.get('confidence', 0.5))
            reasoning = parsed.get('reasoning', '')
            
            if category not in CATEGORIES:
                category = 'Other'
            
            return category, confidence, reasoning
            
        except Exception as e:
            print(f"Groq API error: {e}, falling back to rules")
            return self._rule_based(sender, subject)
    
    def _rule_based(self, sender: str, subject: str) -> Tuple[str, float, str]:
        s_lower = sender.lower()
        sub_lower = subject.lower()
        
        rules = [
            (['otp', 'verification code', 'verification code', '2fa', 'one time password', 'login code', 'security code'], 'OTP/Verification', 0.95),
            (['job offer', 'offer letter', 'interview', 'recruiter', 'hiring', 'application status', 'congratulations.*offer'], 'Job Offers', 0.9),
            (['credit card', 'card statement', 'bill due', 'payment due', 'statement ready', 'minimum due'], 'Credit Card Bills', 0.9),
            (['bank statement', 'account statement', 'monthly statement', 'e-statement'], 'Bank Statements', 0.9),
            (['payment', 'transaction', 'upi', 'transferred', 'received', 'debited', 'credited', 'refund'], 'Payments/Transactions', 0.85),
            (['subscription', 'renewal', 'membership', 'recurring', 'plan renew'], 'Subscriptions', 0.85),
            (['order', 'shipped', 'delivered', 'dispatch', 'tracking', 'flipkart', 'amazon', 'myntra'], 'Shopping/Orders', 0.85),
            (['booking', 'flight', 'train', 'hotel', 'confirmation', 'pnr', 'ticket', 'itinerary'], 'Travel/Bookings', 0.85),
            (['newsletter', 'digest', 'weekly', 'monthly', 'unsubscribe', 'mailing list'], 'Newsletters', 0.8),
            (['promotion', 'sale', 'discount', 'offer', 'coupon', 'deal', '% off', 'buy now'], 'Promotions', 0.8),
            (['facebook', 'instagram', 'linkedin', 'twitter', 'whatsapp', 'notification'], 'Social/Notifications', 0.8),
            (['government', 'income tax', 'aadhaar', 'pan card', 'passport', 'gov.in', 'nic.in'], 'Government/Official', 0.85),
            (['health', 'medical', 'lab', 'report', 'appointment', 'doctor', 'pharmacy', 'insurance'], 'Health/Medical', 0.8),
            (['course', 'certificate', 'udemy', 'coursera', 'learning', 'exam', 'result'], 'Education/Learning', 0.8),
        ]
        
        for keywords, category, conf in rules:
            for kw in keywords:
                if kw in sub_lower or kw in s_lower:
                    return category, conf, f"Matched keyword: {kw}"
        
        if any(x in s_lower for x in ['noreply', 'no-reply', 'donotreply', 'marketing', 'promo']):
            return 'Spam', 0.7, 'Automated/marketing sender'
        
        return 'Other', 0.3, 'No matching rules'

class GmailAIAgent:
    def __init__(self):
        self.db = SupabaseDB()
        self.gmail = GmailClient()
        self.classifier = GroqClassifier()
    
    def process_emails(self, query: str = '', max_results: int = 100, 
                       include_spam_trash: bool = False, only_new: bool = True) -> Dict:
        print(f"Fetching emails (query: '{query or 'all'}', max: {max_results})...")
        emails = self.gmail.fetch_emails(query, max_results, include_spam_trash)
        print(f"Found {len(emails)} emails")
        
        processed = 0
        skipped = 0
        categories = {}
        
        for email_data in emails:
            msg_id = email_data['message_id']
            
            if only_new and self.db.is_processed(msg_id):
                skipped += 1
                continue
            
            category, confidence, reasoning = self.classifier.classify(
                email_data['sender'], email_data['subject']
            )
            
            email = Email(
                message_id=msg_id,
                sender=email_data['sender'],
                subject=email_data['subject'],
                snippet=email_data['snippet'],
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                processed_at=datetime.now().isoformat()
            )
            
            self.db.save_email(email)
            processed += 1
            categories[category] = categories.get(category, 0) + 1
            
            if processed % 10 == 0:
                print(f"  Processed {processed}/{len(emails)}...")
        
        print(f"\nDone! Processed: {processed}, Skipped (already done): {skipped}")
        print("Categories:", categories)
        return {'processed': processed, 'skipped': skipped, 'categories': categories}
    
    def get_stats(self) -> Dict:
        return self.db.get_stats()
    
    def get_emails_by_category(self, category: str, limit: Optional[int] = None) -> List[Email]:
        return self.db.get_emails_by_category(category, limit)
    
    def close(self):
        self.db.close()

def main():
    import sys
    
    # Skip credentials.json check if using refresh token (cloud deployment)
    use_refresh_token = all([
        os.getenv("GOOGLE_CLIENT_ID"),
        os.getenv("GOOGLE_CLIENT_SECRET"),
        os.getenv("GOOGLE_REFRESH_TOKEN")
    ])
    
    if not use_refresh_token and not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: {CREDENTIALS_FILE} not found!")
        print("Download from Google Cloud Console > APIs & Services > Credentials")
        return
    
    if not GROQ_API_KEY or GROQ_API_KEY == 'your_groq_api_key_here':
        print("WARNING: GROQ_API_KEY not set in .env file")
        print("Get free key from https://console.groq.com/keys")
        print("Using rule-based classification only.\n")
    
    query = ''
    max_results = 100
    include_spam = False
    only_new = True
    
    if '--all' in sys.argv:
        query = ''
        max_results = 500
        only_new = False
    elif '--unread' in sys.argv:
        query = 'is:unread'
    if '--spam' in sys.argv:
        include_spam = True
    if '--reprocess' in sys.argv:
        only_new = False
    
    agent = GmailAIAgent()
    try:
        result = agent.process_emails(query, max_results, include_spam, only_new)
        print("\n=== STATS ===")
        for cat, count in agent.get_stats().items():
            print(f"  {cat}: {count}")
    finally:
        agent.close()

if __name__ == '__main__':
    main()