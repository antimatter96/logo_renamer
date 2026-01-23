from dotenv import load_dotenv

from src.app import app

# Load environment variables
# for Gemini Usage
load_dotenv()

if __name__ == "__main__":
    app()
