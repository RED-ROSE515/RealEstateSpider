import psycopg2
import os
from psycopg2 import sql

class DatabaseConnector:
    def __init__(self, host, database, user, password, port=5432):
        """Initialize database connection parameters"""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish connection to the PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print("Successfully connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {str(e)}")
            return False
    
    def disconnect(self):
        """Close connection to the PostgreSQL database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def create_multifamilydive_table(self):
        """Create table for MultifamilyDive articles if it doesn't exist"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS multifamilydive_articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                summary TEXT,
                author TEXT,
                author_title TEXT,
                date TEXT,
                categories TEXT,
                content TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("MultifamilyDive articles table created or already exists")
            return True
        except Exception as e:
            print(f"Error creating MultifamilyDive table: {str(e)}")
            self.conn.rollback()
            return False
    
    def create_credaily_table(self):
        """Create table for CRE Daily articles if it doesn't exist"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS credaily_articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                summary TEXT,
                author TEXT,
                date TEXT,
                categories TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("CRE Daily articles table created or already exists")
            return True
        except Exception as e:
            print(f"Error creating CRE Daily table: {str(e)}")
            self.conn.rollback()
            return False
    
    def insert_multifamilydive_article(self, article):
        """Insert a MultifamilyDive article into the database"""
        try:
            # Convert categories list to comma-separated string
            categories = ','.join(article.get('categories', []))
            
            insert_query = """
            INSERT INTO multifamilydive_articles 
            (title, link, summary, author, author_title, date, categories, content, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO UPDATE 
            SET title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                author = EXCLUDED.author,
                author_title = EXCLUDED.author_title,
                date = EXCLUDED.date,
                categories = EXCLUDED.categories,
                content = EXCLUDED.content,
                source = EXCLUDED.source
            """
            
            self.cursor.execute(insert_query, (
                article.get('title', ''),
                article.get('link', ''),
                article.get('summary', ''),
                article.get('author', ''),
                article.get('author_title', ''),
                article.get('date', ''),
                categories,
                article.get('content', ''),
                article.get('source', 'multifamilydive')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting MultifamilyDive article: {str(e)}")
            self.conn.rollback()
            return False
    
    def insert_credaily_article(self, article):
        """Insert a CRE Daily article into the database"""
        try:
            # Convert categories list to comma-separated string
            categories = ','.join(article.get('categories', []))
            
            insert_query = """
            INSERT INTO credaily_articles 
            (title, link, summary, author, date, categories, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO UPDATE 
            SET title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                author = EXCLUDED.author,
                date = EXCLUDED.date,
                categories = EXCLUDED.categories,
                content = EXCLUDED.content
            """
            
            self.cursor.execute(insert_query, (
                article.get('title', ''),
                article.get('link', ''),
                article.get('summary', ''),
                article.get('author', ''),
                article.get('date', ''),
                categories,
                article.get('content', '')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting CRE Daily article: {str(e)}")
            self.conn.rollback()
            return False
    
    def insert_multifamilydive_articles(self, articles):
        """Insert multiple MultifamilyDive articles into the database"""
        success_count = 0
        for article in articles:
            if self.insert_multifamilydive_article(article):
                success_count += 1
        
        print(f"Successfully inserted {success_count} out of {len(articles)} MultifamilyDive articles")
        return success_count
    
    def insert_credaily_articles(self, articles):
        """Insert multiple CRE Daily articles into the database"""
        success_count = 0
        for article in articles:
            if self.insert_credaily_article(article):
                success_count += 1
        
        print(f"Successfully inserted {success_count} out of {len(articles)} CRE Daily articles")
        return success_count

    def create_multihousing_table(self):
        """Create table for Multihousing articles if it doesn't exist"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS multihousing_articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                summary TEXT,
                author TEXT,
                date TEXT,
                categories TEXT,
                image_url TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("Multihousing articles table created or already exists")
            return True
        except Exception as e:
            print(f"Error creating Multihousing table: {str(e)}")
            self.conn.rollback()
            return False
    
    def insert_multihousing_article(self, article):
        """Insert a Multihousing article into the database"""
        try:
            # Convert categories list to comma-separated string
            categories = ','.join(article.get('categories', []))
            
            insert_query = """
            INSERT INTO multihousing_articles 
            (title, link, summary, author, date, categories, image_url, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO UPDATE 
            SET title = EXCLUDED.title,
                summary = EXCLUDED.summary,
                author = EXCLUDED.author,
                date = EXCLUDED.date,
                categories = EXCLUDED.categories,
                image_url = EXCLUDED.image_url,
                content = EXCLUDED.content
            """
            
            self.cursor.execute(insert_query, (
                article.get('title', ''),
                article.get('link', ''),
                article.get('summary', ''),
                article.get('author', ''),
                article.get('date', ''),
                categories,
                article.get('image_url', ''),
                article.get('content', '')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting Multihousing article: {str(e)}")
            self.conn.rollback()
            return False
    
    def insert_multihousing_articles(self, articles):
        """Insert multiple Multihousing articles into the database"""
        success_count = 0
        for article in articles:
            if self.insert_multihousing_article(article):
                success_count += 1
        
        print(f"Successfully inserted {success_count} out of {len(articles)} Multihousing articles")
        return success_count 