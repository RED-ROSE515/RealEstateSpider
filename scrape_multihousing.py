import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from db_connector import DatabaseConnector

class MultihousingScraper:
    
    def __init__(self):
        self.briefs_data = []
        
    def parse_brief_links(self, html_content, page_num):
        """Parse brief links from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            brief_items = soup.find_all('div', class_='cpe-posts-category-page')
            
            links = []
            for item in brief_items:
                # Find the title and link
                title_element = item.find('h2', class_='fl-post-title')
                if title_element and title_element.find('a'):
                    link = title_element.find('a')['href']
                    title = title_element.find('a').text.strip()
                    
                    # Extract brief summary
                    summary_element = item.find('div', class_='fl-post-excerpt')
                    summary = ""
                    if summary_element and summary_element.find('p'):
                        summary = summary_element.find('p').text.strip()
                    
                    # Extract author and date
                    meta_element = item.find('div', class_='fl-post-meta')
                    author = ""
                    date = ""
                    if meta_element:
                        author_element = meta_element.find('a')
                        author = author_element.text.strip() if author_element else ""
                        
                        # Date is the text after the separator
                        if meta_element.find('span', class_='fl-post-meta-sep'):
                            date_text = meta_element.contents[-1]
                            if isinstance(date_text, str):
                                date = date_text.strip()
                    
                    # Extract categories
                    categories_element = item.find('div', class_='cpe-categories')
                    categories = []
                    if categories_element:
                        category_links = categories_element.find_all('a')
                        categories = [cat.text.strip() for cat in category_links]
                    
                    # Extract image if available
                    image_url = ""
                    image_element = item.find('div', class_='fl-post-image')
                    if image_element and image_element.find('img'):
                        image_url = image_element.find('img')['src']
                    
                    links.append({
                        'link': link,
                        'title': title,
                        'summary': summary,
                        'author': author,
                        'date': date,
                        'categories': categories,
                        'image_url': image_url
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
            
            # First try the new content structure with fl-module-content
            main_content = soup.find('div', id='cmw_main_content')
            if main_content:
                # Extract title if not in brief_info
                if not brief_info.get('title'):
                    title_element = main_content.find('h1', class_='fl-heading')
                    if title_element:
                        brief_info['title'] = title_element.get_text().strip()
                
                # Extract author if not already found
                if not brief_info.get('author'):
                    author_element = main_content.find('a', class_='tdb-author-name')
                    if author_element:
                        brief_info['author'] = author_element.get_text().strip()
                
                # Extract date if not already found
                if not brief_info.get('date'):
                    date_element = main_content.find('span', class_='fl-post-info-date')
                    if date_element:
                        brief_info['date'] = date_element.get_text().strip()
                
                # Extract categories
                categories_element = main_content.find('div', class_='post_categories')
                if categories_element and not brief_info.get('categories'):
                    category_links = categories_element.find_all('a', class_='post_cat')
                    brief_info['categories'] = [cat.text.strip() for cat in category_links]
                
                # Extract all content paragraphs
                content_elements = []
                
                # Get the main post content
                post_content = main_content.find('div', class_='cmw_single_post_content')
                if post_content:
                    content_elements.append(post_content)
                
                # Also get any additional rich text sections
                rich_text_sections = main_content.find_all('div', class_='fl-rich-text')
                content_elements.extend(rich_text_sections)
                
                # Process all content sections
                paragraphs = []
                for element in content_elements:
                    # Get all paragraphs
                    for p in element.find_all('p'):
                        if p.text.strip():
                            paragraphs.append(p.text.strip())
                
                if paragraphs:
                    content = ' '.join(paragraphs)
            
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
    
    def save_to_csv(self, briefs_data, filename="multihousing_articles.csv"):
        """Save briefs data to CSV"""
        if not briefs_data:
            print("No data to save")
            return
        
        df = pd.DataFrame(briefs_data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(briefs_data)} briefs to {filename}")
    
    def save_to_json(self, briefs_data, filename="multihousing_articles.json"):
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
                db.create_multihousing_table()
                
                # Insert articles
                success_count = db.insert_multihousing_articles(briefs_data)
                
                print(f"Saved {success_count} out of {len(briefs_data)} articles to PostgreSQL database")
            finally:
                # Ensure connection is closed
                db.disconnect()
        else:
            print("Failed to connect to database. Articles not saved.") 