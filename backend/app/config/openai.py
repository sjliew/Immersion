import openai
from .settings import settings

# Configure OpenAI
openai.api_key = settings.openai_api_key

# Create client instance
client = openai.OpenAI(api_key=settings.openai_api_key)

__all__ = ["client"]