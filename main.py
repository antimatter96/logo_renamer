from dotenv import load_dotenv

from src.app import app

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    app()
