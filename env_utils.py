import os
from dotenv import load_dotenv
from pathlib import Path

def load_env_file(env_path=None):
    """
    Load environment variables from .env file
    
    Args:
        env_path: Path to .env file. If None, looks for .env in current and parent directories
    
    Returns:
        bool: True if .env file was loaded successfully, False otherwise
    """
    # If no path provided, look for .env file in current directory and parent directories
    if env_path is None:
        # Try in the current directory
        if os.path.exists('.env'):
            env_path = '.env'
        # Try in the parent directory (project root)
        elif os.path.exists('../.env'):
            env_path = '../.env'
        # Try in the spider's directory
        elif os.path.exists(os.path.join(os.path.dirname(__file__), '.env')):
            env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if env_path and os.path.exists(env_path):
        load_dotenv(env_path)
        return True
    
    return False

def get_db_config_from_env():
    """
    Get database configuration from environment variables
    
    Environment variables:
        DB_HOST: Database host
        DB_NAME: Database name
        DB_USER: Database user
        DB_PASSWORD: Database password
        DB_PORT: Database port (optional, defaults to 5432)
        SAVE_TO_DB: Whether to save to database (optional, defaults to False)
    
    Returns:
        dict: Database configuration
    """
    save_to_db = os.getenv('SAVE_TO_DB', 'False').lower() in ('true', 'yes', '1', 't')
    
    return {
        'save_to_db': save_to_db,
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('DB_PORT', '5432'))
    } 