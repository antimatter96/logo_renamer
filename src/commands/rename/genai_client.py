import json
import os

from google import genai
from google.genai import types

from .models import CompanyResponse


def get_client() -> genai.Client | None:
    """
    Initializes and returns the GenAI client.
    Returns None if the API key is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def identify_company(
    client: genai.Client, image_bytes: bytes, mime_type: str, model_name: str
) -> str | None:
    """
    Identifies a company or brand from a logo image using the GenAI model.
    """
    prompt = "Identify the company or brand in this logo image, Give your reasoning"

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CompanyResponse,
            ),
        )

        company_name = ""

        if response.parsed:
            if isinstance(response.parsed, dict):
                company_name = response.parsed.get("company_name", "")
            else:
                company_name = getattr(response.parsed, "company_name", "")
        elif response.text:
            try:
                data = json.loads(response.text)
                company_name = data.get("company_name", "")
            except json.JSONDecodeError:
                # Log error or let caller handle empty return
                return None
        else:
            return None

        company_name = company_name.strip().lower()
        # Basic sanitization
        company_name = "".join(c if c.isalnum() or c == "_" else "_" for c in company_name)

        return company_name if company_name else None

    except Exception:
        # Caller handles exceptions or we log them?
        # For now, let's propagate exceptions or return None.
        # The original code caught exceptions broadly in main.
        # It's better to raise up so main can print the error.
        raise
