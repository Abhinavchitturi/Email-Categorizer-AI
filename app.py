"""
Gmail AI Agent - Streamlit Mobile App
Run: streamlit run app.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_ai_agent import GmailAIAgent, CATEGORIES, CATEGORY_DESCRIPTIONS

st.set_page_config(
    page_title="Gmail AI Classifier",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { max-width: 100%; }
    .metric-card { padding: 1rem; border-radius: 10px; background: #f0f2f6; }
    .email-card { padding: 1rem; border-radius: 10px; background: white; border-left: 4px solid; margin-bottom: 0.5rem; }
    .category-Job-Offers { border-color: #4CAF50; }
    .category-Spam { border-color: #f44336; }
    .category-OTP-Verification { border-color: #FF9800; }
    .category-Payments-Transactions { border-color: #2196F3; }
    .category-Credit-Card-Bills { border-color: #9C27B0; }
    .category-Bank-Statements { border-color: #00BCD4; }
    .category-Subscriptions { border-color: #795548; }
    .category-Shopping-Orders { border-color: #E91E63; }
    .category-Travel-Bookings { border-color: #009688; }
    .category-Newsletters { border-color: #607D8B; }
    .category-Promotions { border-color: #FF5722; }
    .category-Social-Notifications { border-color: #3F51B5; }
    .category-Government-Official { border-color: #673AB7; }
    .category-Health-Medical { border-color: #F44336; }
    .category-Education-Learning { border-color: #03A9F4; }
    .category-Other { border-color: #9E9E9E; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 50px; padding: 0 20px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    return GmailAIAgent()

@st.cache_data(ttl=30)
def get_stats():
    agent = get_agent()
    return agent.get_stats()

@st.cache_data(ttl=30)
def get_emails_by_category(category, limit=50):
    agent = get_agent()
    emails = agent.get_emails_by_category(category, limit)
    # Convert dataclass to dict for Streamlit caching serialization
    return [e.__dict__ for e in emails]

def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %H:%M')
    except:
        return date_str

def render_email_card(email, show_confidence=True):
    # email is a dict
    cat = email.get('category', '')
    cat_class = f"category-{cat.replace(' ', '-').replace('/', '-')}"
    confidence = email.get('confidence', 0)
    conf_color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
    processed_at = email.get('processed_at', '')
    # format date
    try:
        dt = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
        date_str = dt.strftime('%b %d, %H:%M')
    except:
        date_str = processed_at
    reasoning = email.get('reasoning', '')[:100]
    msg_id = email.get('message_id', '')
    gmail_url = f"https://mail.google.com/mail/u/0/#all/{msg_id}" if msg_id else "#"
    st.markdown(f"""
    <div class="email-card {cat_class}">
        <strong>{email.get('subject', '')}</strong><br>
        <small>From: {email.get('sender', '')[:60]}...</small><br>
        <small>{date_str}</small>
        {f'<br><small style="color:{conf_color}">Confidence: {confidence:.0%}</small>' if show_confidence else ''}
        <br><small>{reasoning}...</small>
        <br><a href="{gmail_url}" target="_blank" style="display:inline-block;margin-top:6px;padding:4px 10px;background:#1a73e8;color:#fff;border-radius:4px;text-decoration:none;font-size:0.8rem;">Open in Gmail</a>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("📧 Gmail AI Classifier")
    st.caption("Automatically categorize emails: Job Offers, Spam, OTP, Payments, Credit Card Bills + more")
    
    agent = get_agent()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📬 Emails", "⚙️ Process", "📈 Analytics"])
    
    with tab1:
        stats = get_stats()
        total = sum(stats.values())
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Emails", total)
        col2.metric("Categories", len([c for c in stats.values() if c > 0]))
        col3.metric("Top Category", max(stats, key=stats.get) if stats else "None")
        col4.metric("Uncategorized", stats.get('Other', 0) + stats.get('Uncategorized', 0))
        
        if stats:
            df = pd.DataFrame(list(stats.items()), columns=['Category', 'Count'])
            df = df[df['Count'] > 0].sort_values('Count', ascending=True)
            
            fig = px.bar(df, x='Count', y='Category', orientation='h', 
                        title="Emails by Category", color='Count',
                        color_continuous_scale='viridis')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, width="stretch")
    
    with tab2:
        selected_cat = st.selectbox("Filter by Category", ["All"] + CATEGORIES)
        
        if selected_cat == "All":
            all_emails = []
            for cat in CATEGORIES:
                all_emails.extend(get_emails_by_category(cat, 20))
            all_emails.sort(key=lambda e: e.get('processed_at', ''), reverse=True)
            emails_to_show = all_emails[:100]
        else:
            emails_to_show = get_emails_by_category(selected_cat, 100)
        
        st.write(f"Showing {len(emails_to_show)} emails")
        
        for email in emails_to_show:
            render_email_card(email)
    
    with tab3:
        st.subheader("Process Emails")
        
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Gmail Query", placeholder="is:unread, from:amazon.com, newer_than:7d", 
                                 help="Gmail search syntax")
            max_results = st.slider("Max Emails", 10, 500, 100, 10)
        with col2:
            include_spam = st.checkbox("Include Spam/Trash", value=False)
            only_new = st.checkbox("Only New (skip already processed)", value=True)
        
        if st.button("🚀 Start Processing", type="primary", width="stretch"):
            with st.spinner("Fetching and classifying emails..."):
                progress = st.progress(0)
                status = st.empty()
                
                def update_progress(pct, msg):
                    progress.progress(pct)
                    status.text(msg)
                
                result = agent.process_emails(
                    query=query, 
                    max_results=max_results,
                    include_spam_trash=include_spam,
                    only_new=only_new
                )
            
            st.success(f"Done! Processed: {result['processed']}, Skipped: {result['skipped']}")
            st.json(result['categories'])
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        st.caption("💡 Tips:")
        st.caption("- Use `is:unread` for unread only")
        st.caption("- Use `newer_than:7d` for last 7 days")
        st.caption("- Use `from:domain.com` for specific sender")
        st.caption("- Use `in:anywhere` with spam checkbox for all folders")
    
    with tab4:
        stats = get_stats()
        if not stats or sum(stats.values()) == 0:
            st.info("No data yet. Process some emails first!")
        else:
            df = pd.DataFrame(list(stats.items()), columns=['Category', 'Count'])
            df = df[df['Count'] > 0]
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(df, values='Count', names='Category', title="Category Distribution")
                st.plotly_chart(fig, width="stretch")
            
            with col2:
                fig = px.treemap(df, path=['Category'], values='Count', title="Treemap View")
                st.plotly_chart(fig, width="stretch")
            
            st.subheader("Confidence Distribution")
            all_emails = []
            for cat in CATEGORIES:
                all_emails.extend(get_emails_by_category(cat, 1000))
            
            if all_emails:
                conf_df = pd.DataFrame([{'Category': e.category, 'Confidence': e.confidence} for e in all_emails])
                fig = px.box(conf_df, x='Category', y='Confidence', title="Confidence by Category")
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, width="stretch")

if __name__ == "__main__":
    # On Streamlit Cloud, credentials come from secrets/env vars, not file
    from dotenv import load_dotenv
    load_dotenv()
    
    main()