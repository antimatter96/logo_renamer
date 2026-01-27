# Logo Renamer

A CLI tool to automatically rename company logo images based on brand recognition using Gemini or local OpenAI-compatible models.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file and add your configuration:
   ```bash
   # For Gemini
   GEMINI_API_KEY=your_key_here
   GEMINI_MODAL_NAME=gemini-2.0-flash-exp

   # For Local (Optional)
   LOCAL_OPENAI_BASE_URL=http://localhost:1234/v1
   LOCAL_OPENAI_API_KEY=lm-studio
   LOCAL_OPENAI_MODEL_NAME=your-local-model
   ```

## Usage

Rename a single logo using Gemini (default):
```bash
python main.py rename path/to/logo.png
```

Rename all logos in a directory:
```bash
python main.py rename path/to/logos_dir/
```

Rename using a local model:
```bash
python main.py rename path/to/logo.png --provider local
```

See what would happen without actually renaming:
```bash
python main.py rename path/to/logo.png --dry-run
```

### Trim Background

Trim the background from a single logo (identifies background from top-left pixel):
```bash
python main.py trim path/to/logo.png
```

Trim all logos in a directory:
```bash
python main.py trim path/to/logos_dir/
```

Customize the margin (default is 10 pixels):
```bash
python main.py trim path/to/logo.png --margin 20
```

Replace the original file instead of creating a `_trimmed` version:
```bash
python main.py trim path/to/logo.png --replace
```

## How it works
It uses either the `google-genai` SDK or `openai` SDK to send the image to a vision-capable model. The model identifies the brand (even if no text is present) and returns a sanitized `snake_case` name, which is then used to rename the file. It leverages structured outputs (Pydantic models) for reliable parsing.
