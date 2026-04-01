import os
import ssl
import feedparser
from anthropic import Anthropic
from dotenv import load_dotenv

# internal with user for Claude API key
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("Error: API key not found. Please check your .env file!")
    exit()

# Initialize Claude client
client = Anthropic(api_key=api_key)

def fetch_tech_news(rss_url, limit=5):
    """Fetch the latest news from a given RSS feed url."""
    print(f"Fetching news from {rss_url} ...")
    
    # Bypass Mac SSL certificate verification
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("⚠️ Oops, failed to fetch content!")
        if getattr(feed, 'bozo_exception', None):
            print(f"Network error details: {feed.bozo_exception}")
        return ""
        
    news_items = []
    for entry in feed.entries[:limit]:
        title = entry.title
        summary = entry.get('summary', 'No summary available') 
        news_items.append(f"Title: {title}\nSummary: {summary}\n")
    
    return "\n".join(news_items)

def generate_digest(news_text):
    """Use Claude to summarize raw news into a clean digest."""
    print("Calling Claude to summarize the content...")
    
    # Prompt for Claude to generate the digest
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

    response = client.messages.create(
        model="claude-haiku-4-5-20251001", 
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

if __name__ == "__main__":
    rss_source = "https://hnrss.org/frontpage" 
    
    raw_news = fetch_tech_news(rss_source, limit=6)
    
    if raw_news:
        final_digest = generate_digest(raw_news)
        
        # Output the result
        print("\n" + "="*50)
        print("📰 Your Daily AI Tech Digest is Ready:\n")
        print(final_digest)
        print("="*50)