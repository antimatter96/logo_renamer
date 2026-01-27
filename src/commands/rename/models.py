from pydantic import BaseModel, Field


class CompanyResponse(BaseModel):
    company_name: str = Field(description="The company name in lowercase snake_case.")
    company_info: str = Field(description="What you know about the company?")
    reasoning: str = Field(
        description="Reasoning behind why you think this is the right company."
    )
    confidence_level: int = Field(
        description="How confident are you (in percentage)?", ge=0, le=100
    )
