import base64
import json
import os

from openai import OpenAI

from .models import CompanyResponse


def get_client() -> OpenAI | None:
    """
    Initializes and returns the OpenAI client for local models.
    Returns None if configuration is missing (though for local, we often default).
    """
    base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
    api_key = os.getenv("LOCAL_OPENAI_API_KEY", "lm-studio")

    # We can always return a client because we have defaults,
    # but strictly speaking we might want to ensure the user intends to use it.
    # For now, we'll return the client.
    return OpenAI(base_url=base_url, api_key=api_key)


def identify_company(
    client: OpenAI, image_bytes: bytes, mime_type: str, model_name: str
) -> str | None:
    """
    Identifies a company or brand from a logo image using a local OpenAI-compatible model.
    """
    prompt = "Identify the company or brand in this logo image"

    # Encode image
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        completion = client.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                        },
                    ],
                }
            ],
            response_format=CompanyResponse,
        )

        company_response = completion.choices[0].message.parsed

        if not company_response or not company_response.company_name:
            return None

        company_name = company_response.company_name.strip().lower()
        # Basic sanitization
        company_name = "".join(c if c.isalnum() or c == "_" else "_" for c in company_name)

        return company_name if company_name else None

    except Exception as e:
        # Caller handles exceptions
        raise
