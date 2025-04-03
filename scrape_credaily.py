import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from db_connector import DatabaseConnector

class CredailyScraper:
    
    def __init__(self):
        self.briefs_data = []
        
    def parse_brief_links(self, html_content, page_num):
        """Parse brief links from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            brief_items = soup.find_all('div', class_='c-brief-list__item')
            
            links = []
            for item in brief_items:
                title_element = item.find('h5', class_='c-brief-list__item-title')
                if title_element and title_element.find('a'):
                    link = title_element.find('a')['href']
                    title = title_element.find('a').text.strip()
                    
                    # Extract brief summary
                    summary_element = item.find('p', class_='c-brief-list__item-text')
                    summary = summary_element.text.strip() if summary_element else ""
                    
                    # Extract author
                    author_element = item.find('div', class_='c-brief-list__item-author')
                    author = author_element.text.replace('By', '').strip() if author_element else ""
                    
                    # Extract date
                    date_element = item.find('div', class_='c-brief-list__item-date')
                    date = date_element.text.strip() if date_element else ""
                    
                    # Extract categories
                    categories_element = item.find('div', class_='c-brief-list__item-category')
                    categories = []
                    if categories_element:
                        category_links = categories_element.find_all('a', class_='c-articles__category')
                        categories = [cat.text.strip() for cat in category_links]
                    
                    links.append({
                        'link': link,
                        'title': title,
                        'summary': summary,
                        'author': author,
                        'date': date,
                        'categories': categories
                    })
            return links
        except Exception as e:
            print(f"Error parsing brief links from page {page_num}: {str(e)}")
            return []
    
    def parse_brief_content(self, html_content, brief_info):
        """Parse the content from a brief page HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try multiple potential content selectors
            content = ""
            
            # First try the article content div
            content_element = soup.find('div', class_='c-article__content')
            if content_element:
                paragraphs = content_element.find_all('p')
                if paragraphs:
                    content = ' '.join([p.text.strip() for p in paragraphs])
            
            # If content is still empty, try the brief text section
            if not content:
                # Try the article body section
                article_body = soup.find('div', class_='c-article__body')
                if article_body:
                    paragraphs = article_body.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.text.strip() for p in paragraphs])
            
            # If content is still empty, try another approach - look for the main content area
            if not content:
                main_content = soup.find('main', id='main-content')
                if main_content:
                    # Exclude header elements
                    for header in main_content.find_all(['header', 'nav', 'aside']):
                        header.decompose()
                    
                    paragraphs = main_content.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.text.strip() for p in paragraphs])
            
            # If still no content, try to find any div with text that might be the article
            if not content:
                # Look for any div that might contain the article text
                article_divs = soup.find_all('div', class_=lambda c: c and ('article' in c or 'content' in c))
                for div in article_divs:
                    paragraphs = div.find_all('p')
                    if paragraphs and len(paragraphs) >= 2:  # Minimum 2 paragraphs to be considered content
                        content = ' '.join([p.text.strip() for p in paragraphs])
                        break
            
            # Final fallback - just get any paragraphs from the body
            if not content:
                body = soup.find('body')
                if body:
                    # Exclude header, footer, nav elements
                    for element in body.find_all(['header', 'footer', 'nav', 'aside']):
                        element.decompose()
                    
                    paragraphs = body.find_all('p')
                    # Filter out very short paragraphs that might be navigation/metadata
                    content_paragraphs = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 40]
                    if content_paragraphs:
                        content = ' '.join(content_paragraphs)
            
            brief_info_copy = brief_info.copy()
            brief_info_copy['content'] = content
            return brief_info_copy
            
        except Exception as e:
            print(f"Error parsing content from {brief_info.get('link', 'unknown URL')}: {str(e)}")
            brief_info_copy = brief_info.copy()
            brief_info_copy['content'] = ""
            return brief_info_copy
    
    def save_to_csv(self, briefs_data, filename="credaily_articles.csv"):
        """Save briefs data to CSV"""
        if not briefs_data:
            print("No data to save")
            return
        
        df = pd.DataFrame(briefs_data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(briefs_data)} briefs to {filename}")
    
    def save_to_json(self, briefs_data, filename="credaily_articles.json"):
        """Save briefs data to JSON"""
        if not briefs_data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(briefs_data, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(briefs_data)} briefs to {filename}")
    
    def save_to_postgres(self, briefs_data, db_config):
        """Save briefs data to PostgreSQL database
        
        Args:
            briefs_data: List of article dictionaries
            db_config: Dictionary with keys host, database, user, password, port
        """
        if not briefs_data:
            print("No data to save to database")
            return
        
        # Create database connector
        db = DatabaseConnector(
            host=db_config.get('host'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            port=db_config.get('port', 5432)
        )
        
        # Connect to database
        if db.connect():
            try:
                # Create table if it doesn't exist
                db.create_credaily_table()
                
                # Insert articles
                success_count = db.insert_credaily_articles(briefs_data)
                
                print(f"Saved {success_count} out of {len(briefs_data)} articles to PostgreSQL database")
            finally:
                # Ensure connection is closed
                db.disconnect()
        else:
            print("Failed to connect to database. Articles not saved.") 