# Web Scraper with AWS PostgreSQL Storage

This project scrapes articles from MultifamilyDive and CRE Daily websites and can store them in AWS PostgreSQL.

## Setup

1. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Database Configuration with .env File (Recommended):

   Copy the `.env.example` file to `.env` and edit it with your database settings:

   ```
   cp .env.example .env
   ```

   Then edit the `.env` file with your database credentials:

   ```
   # Database Settings
   SAVE_TO_DB=True
   DB_HOST=your-aws-hostname.rds.amazonaws.com
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_PORT=5432
   ```

## Usage

### Running Spiders with Database Settings from .env

When you have your database settings in a `.env` file, you can simply run:

```bash
# Run MultifamilyDive spider with database settings from .env
scrapy crawl multifamilydive_news -a page_limit=5

# Run CRE Daily spider with database settings from .env
scrapy crawl credaily_news -a page_limit=5
```

You can also specify a custom path to the `.env` file:

```bash
scrapy crawl multifamilydive_news -a env_file=/path/to/your/.env
```

### Running Spiders with Command-line Database Settings

You can still override or specify database settings via command-line arguments:

```bash
# Run MultifamilyDive spider with explicit database settings
scrapy crawl multifamilydive_news -a save_to_db=True -a db_host=your-aws-hostname.rds.amazonaws.com -a db_name=your_db_name -a db_user=your_username -a db_password=your_password -a page_limit=5

# Run CRE Daily spider with explicit database settings
scrapy crawl credaily_news -a save_to_db=True -a db_host=your-aws-hostname.rds.amazonaws.com -a db_name=your_db_name -a db_user=your_username -a db_password=your_password -a page_limit=5
```

Command-line arguments will override settings from the `.env` file.

# Saving Scraped Data to PostgreSQL

This script saves scraped data from MultifamilyDive, CRE Daily, and Multihousing to a PostgreSQL database.

## Prerequisites

Make sure to install the required packages:

```bash
pip install psycopg2-binary python-dotenv
```

### Using Command Line Arguments

You can also provide database credentials directly via command line arguments.

## Usage

### Running with .env configuration:

```bash
python save_to_aws.py --multifamily-file "multifamilydive_articles.json" --credaily-file "credaily_articles.json" --multihousing-file "multihousing_articles.json"
```

### Running with command line arguments:

```bash
python save_to_aws.py --multifamily-file "multifamilydive_articles.json" --credaily-file "credaily_articles.json" --multihousing-file "multihousing_articles.json" --host "your-aws-host" --database "your-db-name" --user "your-username" --password "your-password"
```

### Running with specific data sources:

You can also run the script with just one or two of the data sources:

```bash
# Save only Multihousing data
python save_to_aws.py --multihousing-file "multihousing_articles.json"

# Save both CRE Daily and MultifamilyDive data
python save_to_aws.py --credaily-file "credaily_articles.json" --multifamily-file "multifamilydive_articles.json"
```

## Table Schemas

The script will create the necessary tables in your PostgreSQL database if they don't exist:

1. `multifamilydive_articles` - For MultifamilyDive scraped data
2. `credaily_articles` - For CRE Daily scraped data
3. `multihousing_articles` - For Multihousing scraped data

Each table includes columns for the article title, link, summary, author, date, categories, content, and more.

After scraping data to JSON files using the scraper modules, you can upload the data to AWS PostgreSQL using the `save_to_aws.py` script:

```
python save_to_aws.py --multifamily-file ../multifamilydive_articles.json --credaily-file ../credaily_articles.json --host your-aws-hostname.rds.amazonaws.com --database your_db_name --user your_username --password your_password
```

You can also use the database functionality directly in your scraping script:

```python
from scrape_multifamilydive import MultifamilydiveScraper
from scrape_credaily import CredailyScraper

# Configure database connection
db_config = {
    'host': 'your-aws-hostname.rds.amazonaws.com',
    'database': 'your_db_name',
    'user': 'your_username',
    'password': 'your_password',
    'port': 5432  # Default PostgreSQL port
}

# MultifamilyDive scraper
mfd_scraper = MultifamilydiveScraper()
# Perform scraping to get articles_data
# ...
# Save to PostgreSQL
mfd_scraper.save_to_postgres(articles_data, db_config)

# CRE Daily scraper
cre_scraper = CredailyScraper()
# Perform scraping to get briefs_data
# ...
# Save to PostgreSQL
cre_scraper.save_to_postgres(briefs_data, db_config)
```

## Database Schema

### MultifamilyDive Articles Table

| Column       | Type               | Description                |
| ------------ | ------------------ | -------------------------- |
| id           | SERIAL PRIMARY KEY | Auto-incrementing ID       |
| title        | TEXT               | Article title              |
| link         | TEXT UNIQUE        | Article URL                |
| summary      | TEXT               | Article summary            |
| author       | TEXT               | Author name                |
| author_title | TEXT               | Author title/position      |
| date         | TEXT               | Publication date           |
| categories   | TEXT               | Comma-separated categories |
| content      | TEXT               | Full article content       |
| source       | TEXT               | Source website             |
| created_at   | TIMESTAMP          | Record creation timestamp  |

### CRE Daily Articles Table

| Column     | Type               | Description                |
| ---------- | ------------------ | -------------------------- |
| id         | SERIAL PRIMARY KEY | Auto-incrementing ID       |
| title      | TEXT               | Article title              |
| link       | TEXT UNIQUE        | Article URL                |
| summary    | TEXT               | Article summary            |
| author     | TEXT               | Author name                |
| date       | TEXT               | Publication date           |
| categories | TEXT               | Comma-separated categories |
| content    | TEXT               | Full article content       |
| created_at | TIMESTAMP          | Record creation timestamp  |
