# Vector Embedding with Qdrant

This feature allows you to:

1. Retrieve articles from PostgreSQL database
2. Generate vector embeddings using OpenAI's API
3. Store embeddings in Qdrant vector database
4. Search for similar articles using vector similarity

## Setup

### Prerequisites

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up Qdrant:

   - Option 1: Run Qdrant locally with Docker:
     ```bash
     docker run -p 6333:6333 qdrant/qdrant
     ```
   - Option 2: Use Qdrant Cloud (https://qdrant.tech/documentation/cloud/)

3. Configure your `.env` file:

```
# Database Configuration
DB_HOST=your_postgresql_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Qdrant Configuration
QDRANT_URL=your_qdrant_url_or_localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key  # Only needed for Qdrant Cloud
```

## Usage

### Command Line

Process articles and save embeddings to Qdrant:

```bash
python qdrant_embedding.py --source multifamilydive --limit 50 --batch-size 10
```

Search for similar articles:

```bash
python qdrant_embedding.py --source multifamilydive --search "Apartment rent trends in urban areas during 2023" --search-limit 5
```

### In Code

```python
from qdrant_embedding import QdrantEmbedding

# Initialize
qdrant_processor = QdrantEmbedding()

# Process articles
qdrant_processor.process_articles("multifamilydive", limit=50)

# Find similar articles
similar_articles = qdrant_processor.search_similar_articles(
    "Apartment rent trends in urban areas during 2023",
    source="multifamilydive",
    limit=5
)

# Print similar articles
for article in similar_articles:
    print(f"Title: {article['title']}")
    print(f"Similarity: {article['similarity']:.4f}")
    print("-" * 50)

# Close connection
qdrant_processor.close()
```

## Available Data Sources

- `multifamilydive`: Articles from MultifamilyDive
- `credaily`: Articles from CRE Daily
- `multihousing`: Articles from Multihousing

## How It Works

1. **Data Retrieval**: Articles are retrieved from PostgreSQL database in batches.
2. **Embedding Generation**: For each article, a vector embedding is created using OpenAI's text-embedding-3-small model (1536 dimensions).
3. **Qdrant Storage**: Embeddings are stored in Qdrant collections along with article metadata.
4. **Similarity Search**: When searching, the query text is converted to an embedding and compared against stored embeddings using cosine similarity.

## Embedding Models and Dimensions

This implementation uses OpenAI's `text-embedding-3-small` model which produces 1536-dimensional vectors. The Qdrant collections are configured accordingly with the same dimensions.

If you want to use a different embedding model, make sure to update both:

1. The `EMBEDDING_MODEL` constant in the code
2. The `EMBEDDING_DIMENSION` constant to match your chosen model's output dimension

Available OpenAI embedding models and their dimensions:

- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-3-large`: 3072 dimensions
- `text-embedding-ada-002`: 1536 dimensions (legacy)

## Performance Considerations

- Processing articles in batches reduces API load and improves performance.
- Embeddings are cached in Qdrant for fast retrieval.
- Qdrant supports approximate nearest neighbor search for efficient similarity queries even with large datasets.
