import openai
from os import getenv
from dotenv import load_dotenv

load_dotenv()
key = getenv("OPEN_AI_KEY")
MODEL = "gpt-4o-2024-08-06"


def get_response(system, user, response_format={"type": "json_object"}):
    client = openai.OpenAI(api_key=key)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            response_format=response_format,
            temperature=0,
            presence_penalty=-1,
            n=1,
            frequency_penalty=1,
            modalities=["text"]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None


def get_response_schema(system, user, response_format={"type": "json_object"}):
    client = openai.OpenAI(api_key=key)
    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            response_format=response_format,
            temperature=0,
            presence_penalty=-1,
            n=1,
            frequency_penalty=1,
            modalities=["text"]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return None
