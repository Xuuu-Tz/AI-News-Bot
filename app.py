import os
import ssl
import feedparser
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

st.set_page_config(page_title="AI Tech News Digest", page_icon="📰", layout="centered")

st.title("📰 AI Tech News Digest")
st.markdown("Fetch the latest tech news and let Claude summarize it into a clean, insightful digest.")

# ==========================================
# sidebar for settings and API key input
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    load_dotenv()
    env_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    # alowe user to input API key or read from .env
    api_key = st.text_input(
        "Anthropic API Key", 
        value=env_api_key, 
        type="password", 
        help="You can enter your key here, or let the app read from the .env file."
    )
    
    # allow user to specify RSS feed and number of articles to fetch
    rss_source = st.text_input("RSS Feed URL", value="https://hnrss.org/frontpage")
    limit = st.slider("Articles to fetch", min_value=1, max_value=15, value=6)

def fetch_tech_news(rss_url, fetch_limit):
    """Fetch the latest news from a given RSS feed url."""
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        st.error("⚠️ Oops, failed to fetch content!")
        if getattr(feed, 'bozo_exception', None):
            st.error(f"Network error details: {feed.bozo_exception}")
        return ""
        
    news_items = []
    for entry in feed.entries[:fetch_limit]:
        title = entry.title
        summary = entry.get('summary', 'No summary available') 
        news_items.append(f"Title: {title}\nSummary: {summary}\n")
    
    return "\n".join(news_items)

def generate_digest(client_instance, news_text):
    """Use Claude to summarize raw news into a clean digest."""
    prompt = f"""
    You are a professional tech media editor. Please read the following raw tech news data I fetched for today:
    
    <news_data>
    {news_text}
    </news_data>
    
    Please generate a "Daily Tech Digest" tailored for software engineers and tech professionals.
    Requirements:
    1. Maintain a professional yet engaging tone.
    2. Select the top 3 most interesting or important news items. Provide a brief explanation and a sharp, one-sentence insightful commentary for each.
    3. Output in clean Markdown format. 
    """

    response = client_instance.messages.create(
        model="claude-haiku-4-5-20251001", 
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

# ==========================================
# homepage main logic
# ==========================================
if st.button("🚀 Generate My Digest", type="primary"):
    if not api_key:
        st.error("Error: API key not found. Please enter it in the sidebar!")
    else:
        with st.spinner(f"Fetching news from {rss_source} ..."):
            raw_news = fetch_tech_news(rss_source, limit)
        
        if raw_news:
            with st.spinner("Calling Claude to analyze and summarize..."):
                try:
                    client = Anthropic(api_key=api_key)
                    final_digest = generate_digest(client, raw_news)
                    
                    st.success("✨ Your Daily AI Tech Digest is Ready!")
                    
                    st.markdown("---")
                    st.markdown(final_digest)
                    st.markdown("---")
                    
                    # additional feature: allow user to download the digest as a markdown file
                    st.download_button(
                        label="💾 Download Digest as Markdown",
                        data=final_digest,
                        file_name="Daily_Tech_Digest.md",
                        mime="text/markdown"
                    )
                except Exception as e:
                    error_msg = str(e)
                    if "401" in error_msg or "authentication_error" in error_msg:
                        st.error("The API Key you entered appears to be incorrect. Please check in the left sidebar to ensure it is copied completely and does not contain extra spaces.")
                    elif "429" in error_msg or "rate_limit_error" in error_msg:
                        st.error("your API credits seem to be exhausted or the request rate is too high. Please try again later.")
                    else:
                        st.error(f"An unknown error occurred. Please contact the developer: {error_msg}")