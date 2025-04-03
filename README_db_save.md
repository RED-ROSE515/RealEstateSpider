# Saving Scraped Data to PostgreSQL

This script saves scraped data from MultifamilyDive, CRE Daily, and Multihousing to a PostgreSQL database.

## Prerequisites

Make sure to install the required packages:

```bash
pip install psycopg2-binary python-dotenv
```

## Configuration

You can configure the database connection in two ways:

### 1. Using .env file (Recommended)

Create a `.env` file in the root directory with the following content:

```
# Database Configuration
DB_HOST=your_postgresql_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432
```

### 2. Using Command Line Arguments

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
