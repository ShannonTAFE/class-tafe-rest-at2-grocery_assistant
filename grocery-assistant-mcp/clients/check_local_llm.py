import os
from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()

    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:3b")

    client = OpenAI(
        base_url=base_url,
        api_key="ollama",  # Ollama does not require a real API key locally.
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a concise grocery assistant.",
            },
            {
                "role": "user",
                "content": "Suggest one simple dinner using rice, chicken, and broccoli.",
            },
        ],
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()