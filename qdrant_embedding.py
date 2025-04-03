import os
import numpy as np
import pandas as pd
from db_connector import DatabaseConnector
from env_utils import load_env_file, get_db_config_from_env
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# Load environment variables
load_env_file()

# Set OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define embedding model and its dimension
EMBEDDING_MODEL = "text-embedding-3-small"  # Changed from text-embedding-3-large to match collection dimension
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small uses 1536 dimensions

class QdrantEmbedding:
    def __init__(self, db_connector=None):
        """Initialize with a database connector and Qdrant client"""
        # Database connection for article retrieval
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
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=600.0,
            max_retries=3,
        )
        # Qdrant client for vector storage
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_port = int(os.getenv("QDRANT_PORT"))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        
        # Define collection names for each source
        self.collections = {
            "multifamilydive": "multifamilydive_articles",
            "credaily": "credaily_articles",
            "multihousing": "multihousing_articles"
        }
        
        # Initialize collections
        for collection_name in self.collections.values():
            self.create_collection(collection_name)

    def create_collection(self, collection_name):
        """Create a Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                # Create new collection with the OpenAI embedding dimension 
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {collection_name}")
            else:
                print(f"Qdrant collection already exists: {collection_name}")
            
            return True
        except Exception as e:
            print(f"Error creating Qdrant collection {collection_name}: {str(e)}")
            return False

    def get_articles(self, source='multifamilydive', limit=100, offset=0):
        """Retrieve articles from specified source
        
        Args:
            source: Source table name (multifamilydive, credaily, multihousing)
            limit: Maximum number of articles to retrieve
            offset: Number of articles to skip
            
        Returns:
            List of dictionaries containing article data
        """
        table_name = f"{source}_articles"
        try:
            query = f"""
            SELECT id, title, summary, content, link, author, date, categories
            FROM {table_name}
            ORDER BY id
            LIMIT %s OFFSET %s
            """
            
            self.db.cursor.execute(query, (limit, offset))
            results = self.db.cursor.fetchall()
            
            articles = []
            for row in results:
                articles.append({
                    'id': row[0],
                    'title': row[1] or "",
                    'summary': row[2] or "",
                    'content': row[3] or "",
                    'link': row[4] or "",
                    'author': row[5] or "",
                    'date': row[6] or "",
                    'categories': row[7] or "",
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
            List containing embedding
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            max_tokens = 8000
            if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
                text = text[:max_tokens * 4]
            
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,  # Use consistent model defined at the top
                input=text
            )

            # Correct way to extract embedding
            embedding = response.data[0].embedding  
            return embedding

        except Exception as e:
            print(f"Error creating embedding: {str(e)}")
            return None

    def save_embedding_to_qdrant(self, article, embedding, collection_name):
        """Save embedding to Qdrant
        
        Args:
            article: Dictionary containing article data
            embedding: Vector embedding array
            collection_name: Name of the Qdrant collection
            
        Returns:
            Boolean indicating success
        """
        try:
            # Prepare metadata (payload)
            payload = {
                "article_id": article['id'],
                "title": article['title'],
                "summary": article['summary'],
                "link": article['link'],
                "author": article['author'],
                "date": article['date'],
                "categories": article['categories'],
                "source": article['source']
            }
            
            # Upsert the point
            self.qdrant.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=article['id'],
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error saving embedding to Qdrant: {str(e)}")
            return False

    def process_articles(self, source='multifamilydive', limit=100, batch_size=10):
        """Process articles from specified source, create embeddings and save them to Qdrant
        
        Args:
            source: Source table name (multifamilydive, credaily, multihousing)
            limit: Maximum number of articles to process
            batch_size: Number of articles to process in one batch
            
        Returns:
            Number of successfully processed articles
        """
        if source not in self.collections:
            print(f"Unknown source: {source}")
            return 0
            
        collection_name = self.collections[source]
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
                text = f"{article['title']} {article['summary']}"
                
                # Create embedding
                embedding = self.create_embedding(text)
                
                if embedding:
                    # Save embedding to Qdrant
                    if self.save_embedding_to_qdrant(article, embedding, collection_name):
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

    def search_similar_articles(self, query_text, source='multifamilydive', limit=5):
        """Find articles similar to the query text using Qdrant
        
        Args:
            query_text: Text to find similar articles for
            source: Source of articles (multifamilydive, credaily, multihousing)
            limit: Maximum number of articles to return
            
        Returns:
            List of dictionaries containing similar articles
        """
        if source not in self.collections:
            print(f"Unknown source: {source}")
            return []
            
        collection_name = self.collections[source]
        
        try:
            # Create embedding for query text
            query_embedding = self.create_embedding(query_text)
            
            if not query_embedding:
                return []
                
            # Search for similar points in Qdrant
            search_results = self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format the results
            similar_articles = []
            for result in search_results:
                payload = result.payload
                similar_articles.append({
                    'id': payload.get('article_id'),
                    'title': payload.get('title', ''),
                    'summary': payload.get('summary', ''),
                    'link': payload.get('link', ''),
                    'author': payload.get('author', ''),
                    'date': payload.get('date', ''),
                    'categories': payload.get('categories', ''),
                    'source': payload.get('source', ''),
                    'similarity': result.score
                })
            
            return similar_articles
        except Exception as e:
            print(f"Error searching similar articles: {str(e)}")
            return []

    def close(self):
        """Close database connection"""
        self.db.disconnect()

def main():
    """Main function for command line usage"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create vector embeddings for articles using Qdrant")
    parser.add_argument("--source", choices=["multifamilydive", "credaily", "multihousing"], 
                        default="multifamilydive", help="Source of articles")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of articles to process")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of articles per batch")
    parser.add_argument("--search", type=str, help="Search query to find similar articles")
    parser.add_argument("--search-limit", type=int, default=5, help="Maximum number of search results")
    args = parser.parse_args()
    
    # Create vector embedding processor
    qdrant_processor = QdrantEmbedding()
    
    try:
        if args.search:
            # Search for similar articles
            similar_articles = qdrant_processor.search_similar_articles(
                args.search, 
                args.source, 
                args.search_limit
            )
            
            print(f"\nSearch results for '{args.search}':")
            for i, article in enumerate(similar_articles, 1):
                print(f"\n{i}. {article['title']}")
                print(f"   Similarity score: {article['similarity']:.4f}")
                print(f"   Author: {article['author']}")
                print(f"   Date: {article['date']}")
                print(f"   Summary: {article['summary'][:150]}...")
        else:
            # Process articles
            qdrant_processor.process_articles(args.source, args.limit, args.batch_size)
    finally:
        # Close database connection
        qdrant_processor.close()


if __name__ == "__main__":
    main() 