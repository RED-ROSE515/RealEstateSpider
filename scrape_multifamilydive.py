import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from db_connector import DatabaseConnector

class MultifamilydiveScraper:
    
    def __init__(self):
        self.articles_data = []
        
    def parse_article_links(self, html_content, page_num):
        """Parse article links from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Find all feed items
            article_items = soup.find_all('li', class_='feed__item')
            
            links = []
            for item in article_items:
                # Skip ad items
                if 'feed-item-ad' in item.get('class', []):
                    continue
                
                # Find the title and link
                title_element = item.find('h3', class_='feed__title')
                if title_element and title_element.find('a'):
                    link = title_element.find('a')['href']
                    if not link.startswith('http'):
                        link = 'https://www.multifamilydive.com' + link
                    title = title_element.find('a').text.strip()
                    
                    # Extract description
                    desc_element = item.find('p', class_='feed__description')
                    summary = desc_element.text.strip() if desc_element else ""
                    
                    # Extract label/category if available
                    label_element = item.find('span', class_='label')
                    category = label_element.text.strip() if label_element else ""
                    
                    # Add to links
                    links.append({
                        'link': link,
                        'title': title,
                        'summary': summary,
                        'author': "",  # Will be extracted from article page
                        'author_title': "",  # Will be extracted from article page
                        'date': "",    # Will be extracted from article page
                        'categories': [category] if category else [],
                        'source': 'multifamilydive'
                    })
            return links
        except Exception as e:
            print(f"Error parsing article links from page {page_num}: {str(e)}")
            return []
    
    def parse_article_content(self, html_content, article_info):
        """Parse the content from a article page HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            article_info_copy = article_info.copy()
            
            # Extract article content
            content = ""
            
            # Find article container (now using article tag instead of div)
            article_container = soup.find('article', class_='brief') or soup.find('article')
            if article_container:
                # Get author info if available using the new structure
                author_element = article_container.find('div', class_='author-name-with-headshot') or article_container.find('div', class_='author-name')
                if author_element:
                    # Extract author name from the anchor tag
                    author_link = author_element.find('a', rel='author')
                    if author_link:
                        article_info_copy['author'] = author_link.text.strip()
                    
                    # Extract author title if available
                    author_title = author_element.find('span', class_='author-title')
                    if author_title:
                        article_info_copy['author_title'] = author_title.text.strip()
                else:
                    # Fallback to original method
                    byline_element = article_container.find('div', class_='article__byline')
                    if byline_element:
                        author = byline_element.text.strip()
                        article_info_copy['author'] = author
                
                # Get date if available
                date_element = article_container.find('div', class_='date') or article_container.find('span', class_='published-info')
                if date_element:
                    date = date_element.text.strip()
                    article_info_copy['date'] = date
                    
                # Extract categories from the post-article-topics div
                categories_div = soup.find('div', class_='post-article-topics')
                if categories_div:
                    category_links = categories_div.find_all('a', class_='topic')
                    if category_links:
                        categories = [link.text.strip().rstrip(',') for link in category_links]
                        # Only update if we found categories
                        if categories:
                            article_info_copy['categories'] = categories
                    
                # Get article body content
                body = article_container.find('div', class_='article-body')
                if body:
                    # Exclude any embedded ads or widgets
                    for ad in body.find_all(['div', 'aside'], class_=lambda c: c and ('ad' in c or 'widget' in c or 'hybrid-ad' in c)):
                        ad.decompose()
                        
                    paragraphs = body.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.text.strip() for p in paragraphs])
            
            # If no content found, try alternative selectors
            if not content:
                # Look for content in article-body class
                article_body = soup.find(['div'], class_='article-body')
                if article_body:
                    # Remove any ads or hybrid content
                    for ad in article_body.find_all(['div'], class_=lambda c: c and ('ad' in c or 'hybrid' in c)):
                        ad.decompose()
                    
                    paragraphs = article_body.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.text.strip() for p in paragraphs])
            
            # Final fallback - look for any content in the page
            if not content:
                # Try the main content area
                main_content = soup.find('main')
                if main_content:
                    # Exclude header, nav, sidebar elements
                    for element in main_content.find_all(['header', 'nav', 'aside']):
                        element.decompose()
                    
                    paragraphs = main_content.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.text.strip() for p in paragraphs])
                
                # If still no content, try the whole body
                if not content:
                    # Find all paragraphs in the body that might be content
                    body = soup.find('body')
                    if body:
                        # Exclude header, footer, sidebar elements
                        for element in body.find_all(['header', 'footer', 'aside', 'nav']):
                            element.decompose()
                            
                        # Get paragraphs with reasonable length
                        paragraphs = body.find_all('p')
                        content_paragraphs = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 40]
                        if content_paragraphs:
                            content = ' '.join(content_paragraphs)
            
            article_info_copy['content'] = content
            return article_info_copy
            
        except Exception as e:
            print(f"Error parsing content from {article_info.get('link', 'unknown URL')}: {str(e)}")
            article_info_copy = article_info.copy()
            article_info_copy['content'] = ""
            return article_info_copy
    
    def save_to_csv(self, articles_data, filename="multifamilydive_articles.csv"):
        """Save articles data to CSV"""
        if not articles_data:
            print("No data to save")
            return
        
        df = pd.DataFrame(articles_data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(articles_data)} articles to {filename}")
    
    def save_to_json(self, articles_data, filename="multifamilydive_articles.json"):
        """Save articles data to JSON"""
        if not articles_data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(articles_data)} articles to {filename}")
    
    def save_to_postgres(self, articles_data, db_config):
        """Save articles data to PostgreSQL database
        
        Args:
            articles_data: List of article dictionaries
            db_config: Dictionary with keys host, database, user, password, port
        """
        if not articles_data:
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
                db.create_multifamilydive_table()
                
                # Insert articles
                success_count = db.insert_multifamilydive_articles(articles_data)
                
                print(f"Saved {success_count} out of {len(articles_data)} articles to PostgreSQL database")
            finally:
                # Ensure connection is closed
                db.disconnect()
        else:
            print("Failed to connect to database. Articles not saved.") 