# vector_embedding.py - New file for vector embedding functionality

import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import openai
from db_connector import DatabaseConnector
from env_utils import load_env_file, get_db_config_from_env
from psycopg2 import sql

# Load environment variables
load_env_file()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class VectorEmbedding:
    def __init__(self, db_connector=None):
        """Initialize with a database connector or create one from environment variables"""
        if db_connector:
            self.db = db_connector
        else:
            # Get database configuration from environment variables
            db_config = get_db_config_from_env()
            self.db = DatabaseConnector(
                host=db_config.get('host'),
                database=db_config.get('database'),
                user=db_config.get('user'),
                password=db_config.get('password'),
                port=db_config.get('port', 5432)
            )
            self.db.connect()
        
        # Create embeddings table if it doesn't exist
        self.create_embeddings_table()

    def create_embeddings_table(self):
        """Create table for storing embeddings if it doesn't exist"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS article_embeddings (
                id SERIAL PRIMARY KEY,
                article_id INTEGER NOT NULL,
                article_source TEXT NOT NULL,
                embedding VECTOR(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(article_id, article_source)
            );
            """
            self.db.cursor.execute(create_table_query)
            self.db.conn.commit()
            print("Article embeddings table created or already exists")
            return True
        except Exception as e:
            print(f"Error creating embeddings table: {str(e)}")
            self.db.conn.rollback()
            return False

    def add_vector_extension(self):
        """Add the pgvector extension to the database if it doesn't exist"""
        try:
            create_extension_query = """
            CREATE EXTENSION IF NOT EXISTS vector;
            """
            self.db.cursor.execute(create_extension_query)
            self.db.conn.commit()
            print("pgvector extension created or already exists")
            return True
        except Exception as e:
            print(f"Error creating pgvector extension: {str(e)}")
            self.db.conn.rollback()
            return False

    def get_articles(self, source='multifamilydive', limit=100, offset=0):
        """Retrieve articles from specified source
        
        Args:
            source: Source table name (multifamilydive_articles, credaily_articles, multihousing_articles)
            limit: Maximum number of articles to retrieve
            offset: Number of articles to skip
            
        Returns:
            List of dictionaries containing article data
        """
        table_name = f"{source}_articles"
        try:
            query = sql.SQL("""
            SELECT id, title, summary, content
            FROM {}
            ORDER BY id
            LIMIT %s OFFSET %s
            """).format(sql.Identifier(table_name))
            
            self.db.cursor.execute(query, (limit, offset))
            results = self.db.cursor.fetchall()
            
            articles = []
            for row in results:
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'content': row[3],
                    'source': source
                })
            
            print(f"Retrieved {len(articles)} articles from {table_name}")
            return articles
        except Exception as e:
            print(f"Error retrieving articles from {table_name}: {str(e)}")
            return []

    def create_embedding(self, text):
        """Create embedding for the given text using OpenAI's API
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Numpy array containing embedding
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            max_tokens = 8000
            if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
                text = text[:max_tokens * 4]
            
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            # Extract the embedding from the response
            embedding = response['data'][0]['embedding']
            return embedding
        except Exception as e:
            print(f"Error creating embedding: {str(e)}")
            return None

    def save_embedding(self, article_id, article_source, embedding):
        """Save embedding to database
        
        Args:
            article_id: ID of the article
            article_source: Source of the article (multifamilydive, credaily, multihousing)
            embedding: Numpy array containing embedding
            
        Returns:
            Boolean indicating success
        """
        try:
            # Convert embedding to string format for Postgres
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            
            insert_query = """
            INSERT INTO article_embeddings 
            (article_id, article_source, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (article_id, article_source) DO UPDATE 
            SET embedding = EXCLUDED.embedding,
                created_at = CURRENT_TIMESTAMP
            """
            
            self.db.cursor.execute(insert_query, (
                article_id,
                article_source,
                embedding_str
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving embedding: {str(e)}")
            self.db.conn.rollback()
            return False

    def process_articles(self, source='multifamilydive', limit=100, batch_size=10):
        """Process articles from specified source, create embeddings and save them
        
        Args:
            source: Source table name (multifamilydive, credaily, multihousing)
            limit: Maximum number of articles to process
            batch_size: Number of articles to process in one batch
            
        Returns:
            Number of successfully processed articles
        """
        offset = 0
        processed_count = 0
        
        while processed_count < limit:
            # Get batch of articles
            batch_limit = min(batch_size, limit - processed_count)
            articles = self.get_articles(source, batch_limit, offset)
            
            if not articles:
                break
                
            for article in articles:
                # Combine title, summary, and content for embedding
                text = f"{article['title']} {article['summary']} {article['content']}"
                
                # Create embedding
                embedding = self.create_embedding(text)
                
                if embedding:
                    # Save embedding
                    if self.save_embedding(article['id'], article['source'], embedding):
                        processed_count += 1
                        print(f"Processed article {article['id']} from {article['source']}")
                    else:
                        print(f"Failed to save embedding for article {article['id']} from {article['source']}")
                else:
                    print(f"Failed to create embedding for article {article['id']} from {article['source']}")
            
            offset += len(articles)
            
            if len(articles) < batch_limit:
                break
                
        print(f"Successfully processed {processed_count} articles from {source}")
        return processed_count

    def find_similar_articles(self, query_text, source='multifamilydive', limit=5):
        """Find articles similar to the query text
        
        Args:
            query_text: Text to find similar articles for
            source: Source table name (multifamilydive, credaily, multihousing)
            limit: Maximum number of articles to return
            
        Returns:
            List of dictionaries containing similar articles
        """
        try:
            # Create embedding for query text
            query_embedding = self.create_embedding(query_text)
            
            if not query_embedding:
                return []
                
            # Convert embedding to string format for Postgres
            query_embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"
            
            table_name = f"{source}_articles"
            
            # Query for similar articles
            query = f"""
            SELECT a.id, a.title, a.summary, a.content,
                   1 - (e.embedding <=> '{query_embedding_str}'::vector) AS similarity
            FROM {table_name} a
            JOIN article_embeddings e ON a.id = e.article_id AND e.article_source = %s
            ORDER BY similarity DESC
            LIMIT %s
            """
            
            self.db.cursor.execute(query, (source, limit))
            results = self.db.cursor.fetchall()
            
            similar_articles = []
            for row in results:
                similar_articles.append({
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'content': row[3],
                    'similarity': row[4],
                    'source': source
                })
            
            return similar_articles
        except Exception as e:
            print(f"Error finding similar articles: {str(e)}")
            return []

    def close(self):
        """Close database connection"""
        self.db.disconnect()


def main():
    """Main function for command line usage"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create vector embeddings for articles")
    parser.add_argument("--source", choices=["multifamilydive", "credaily", "multihousing"], 
                        default="multifamilydive", help="Source of articles")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of articles to process")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of articles per batch")
    args = parser.parse_args()
    
    # Create vector embedding processor
    vector_processor = VectorEmbedding()
    
    try:
        # Ensure pgvector extension is installed
        vector_processor.add_vector_extension()
        
        # Process articles
        vector_processor.process_articles(args.source, args.limit, args.batch_size)
    finally:
        # Close database connection
        vector_processor.close()


if __name__ == "__main__":
    main()