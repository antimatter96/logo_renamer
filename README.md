# Logo Renamer

A CLI tool to automatically rename company logo images based on brand recognition using Gemini 3 Flash.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file and add your Gemini API Key:
   ```bash
   echo "GEMINI_API_KEY=your_key_here" > .env
   ```

## Usage

Rename a single logo:
```bash
python main.py rename path/to/logo.png
```

See what would happen without actually renaming:
```bash
python main.py rename path/to/logo.png --dry-run
```

## How it works
It uses the `google-genai` SDK to send the image to Gemini 3 Flash (`gemini-3-flash-preview`). The model identifies the brand (even if no text is present) and returns a sanitized `snake_case` name, which is then used to rename the file.
