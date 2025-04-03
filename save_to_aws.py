import os
import json
import argparse
from dotenv import load_dotenv
from scrape_multifamilydive import MultifamilydiveScraper
from scrape_credaily import CredailyScraper
from scrape_multihousing import MultihousingScraper

# Load environment variables from .env file
load_dotenv()

def load_json_data(filepath):
    """Load data from a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} items from {filepath}")
        return data
    except Exception as e:
        print(f"Error loading data from {filepath}: {str(e)}")
        return []

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Save scraped data to AWS PostgreSQL database')
    parser.add_argument('--multifamily-file', type=str, help='Path to MultifamilyDive JSON file')
    parser.add_argument('--credaily-file', type=str, help='Path to CRE Daily JSON file')
    parser.add_argument('--multihousing-file', type=str, help='Path to Multihousing JSON file')
    parser.add_argument('--host', type=str, help='AWS PostgreSQL host (overrides .env)')
    parser.add_argument('--database', type=str, help='Database name (overrides .env)')
    parser.add_argument('--user', type=str, help='Database user (overrides .env)')
    parser.add_argument('--password', type=str, help='Database password (overrides .env)')
    parser.add_argument('--port', type=int, help='Database port (overrides .env)')
    
    args = parser.parse_args()
    
    # Database configuration - use command line args if provided, otherwise use environment variables
    db_config = {
        'host': args.host or os.getenv('DB_HOST'),
        'database': args.database or os.getenv('DB_NAME'),
        'user': args.user or os.getenv('DB_USER'),
        'password': args.password or os.getenv('DB_PASSWORD'),
        'port': args.port or int(os.getenv('DB_PORT', 5432))
    }
    
    # Check if required database settings are available
    required_settings = ['host', 'database', 'user', 'password']
    missing_settings = [setting for setting in required_settings if not db_config[setting]]
    
    if missing_settings:
        print(f"Error: Missing required database settings: {', '.join(missing_settings)}")
        print("Please provide these settings via command line arguments or .env file")
        return
    
    # Process MultifamilyDive data
    if args.multifamily_file:
        if os.path.exists(args.multifamily_file):
            multifamily_data = load_json_data(args.multifamily_file)
            if multifamily_data:
                scraper = MultifamilydiveScraper()
                scraper.save_to_postgres(multifamily_data, db_config)
        else:
            print(f"MultifamilyDive file not found: {args.multifamily_file}")
    
    # Process CRE Daily data
    if args.credaily_file:
        if os.path.exists(args.credaily_file):
            credaily_data = load_json_data(args.credaily_file)
            if credaily_data:
                scraper = CredailyScraper()
                scraper.save_to_postgres(credaily_data, db_config)
        else:
            print(f"CRE Daily file not found: {args.credaily_file}")
            
    # Process Multihousing data
    if args.multihousing_file:
        if os.path.exists(args.multihousing_file):
            multihousing_data = load_json_data(args.multihousing_file)
            if multihousing_data:
                scraper = MultihousingScraper()
                scraper.save_to_postgres(multihousing_data, db_config)
        else:
            print(f"Multihousing file not found: {args.multihousing_file}")

if __name__ == "__main__":
    main() 