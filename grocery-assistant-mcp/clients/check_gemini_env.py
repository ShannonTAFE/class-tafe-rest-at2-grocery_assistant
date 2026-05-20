import os
from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with one short sentence confirming the Gemini API works.",
    )

    print(response.text)


if __name__ == "__main__":
    main()