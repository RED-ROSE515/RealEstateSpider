from collections.abc import Iterable
import scrapy
import sys
import os
from pathlib import Path
from urllib.parse import urljoin
import argparse

# Add parent directory to path to import scraper
sys.path.append(str(Path(__file__).parent.parent))
from scrape_multifamilydive import MultifamilydiveScraper
from env_utils import load_env_file, get_db_config_from_env

class MultifamilydiveSpider(scrapy.Spider):
    name = "multifamilydive_news"
    start_urls = ["https://www.multifamilydive.com/?page=1"]  
    
    def __init__(self, *args, **kwargs):
        super(MultifamilydiveSpider, self).__init__(*args, **kwargs)
        self.scraper = MultifamilydiveScraper()
        self.page_limit = kwargs.get('page_limit', 100)
        self.collected_data = []
        
        # Load .env file if it exists
        env_path = kwargs.get('env_file', '.env')
        load_env_file(env_path)
        
        # Get database config from environment variables or kwargs
        db_config = get_db_config_from_env()
        
        # Override with any explicit kwargs (command line args take precedence)
        self.save_to_db = kwargs.get('save_to_db', db_config['save_to_db'])
        if isinstance(self.save_to_db, str):
            self.save_to_db = self.save_to_db.lower() in ('true', 'yes', '1', 't')
            
        self.db_host = kwargs.get('db_host', db_config['host'])
        self.db_name = kwargs.get('db_name', db_config['database'])
        self.db_user = kwargs.get('db_user', db_config['user'])
        self.db_password = kwargs.get('db_password', db_config['password'])
        self.db_port = kwargs.get('db_port', db_config['port'])
        
        if self.save_to_db:
            self.logger.info("Database saving is enabled")
            if all([self.db_host, self.db_name, self.db_user, self.db_password]):
                self.logger.info(f"Using database host: {self.db_host}, database: {self.db_name}")
            else:
                self.logger.warning("Missing some database settings. Check your .env file or command line arguments.")

    def start_requests(self):  
        start_page = 1
        end_page = int(self.page_limit)
        
        for page in range(start_page, end_page + 1):
            self.logger.info(f"Requesting page {page}")
            yield scrapy.Request(  
                url=f'https://www.multifamilydive.com/?page={page}',
                callback=self.parse_article_list,  
                meta={  
                    'zyte_api': {  
                        'timeout': 60,
                    },
                    'page_num': page
                }  
            )

    def parse_article_list(self, response):
        """Parse the list of articles on a page"""
        page_num = response.meta.get('page_num', 1)
        self.logger.info(f"Processing page {page_num}")
        
        # Use MultifamilydiveScraper to parse links from response text
        article_links = self.scraper.parse_article_links(response.text, page_num)
        self.logger.info(f"Found {len(article_links)} articles on page {page_num}")
        
        # Process each article
        for article in article_links:
            # Make sure we have an absolute URL by joining with response URL if the link is relative
            article_url = urljoin(response.url, article['link'])
            
            # Request the content page for each article
            yield scrapy.Request(
                url=article_url,
                callback=self.parse_article_content,
                meta={
                    'zyte_api': {
                        'timeout': 60,
                    },
                    'article_info': article
                }
            )
    
    def parse_article_content(self, response):
        """Parse the content of an individual article"""
        article_info = response.meta.get('article_info', {})
        
        # Use MultifamilydiveScraper to parse content from response text
        article_with_content = self.scraper.parse_article_content(response.text, article_info)
        
        # Add to collected data
        self.collected_data.append(article_with_content)
        
        # Return the item
        return article_with_content
    
    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total articles collected: {len(self.collected_data)}")
        
        # Save the collected data
        if self.collected_data:
            output_prefix = 'multifamilydive_articles'
            self.scraper.save_to_csv(self.collected_data, f"{output_prefix}_articles.csv")
            self.scraper.save_to_json(self.collected_data, f"{output_prefix}_articles.json")
            
            # Save to PostgreSQL if configured
            if self.save_to_db and self.db_host and self.db_name and self.db_user and self.db_password:
                self.logger.info("Saving data to PostgreSQL database")
                db_config = {
                    'host': self.db_host,
                    'database': self.db_name,
                    'user': self.db_user,
                    'password': self.db_password,
                    'port': int(self.db_port) if isinstance(self.db_port, str) else self.db_port
                }
                self.scraper.save_to_postgres(self.collected_data, db_config)
            elif self.save_to_db:
                self.logger.error("Database saving enabled but missing database configuration") 