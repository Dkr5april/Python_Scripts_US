from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("AIzaSyB9hj9C73nQJRn12VDun3nL4U9Y7C4Cgg4"))

print("Available models:")
for m in client.models.list():
    print(f"Name: {m.name}")