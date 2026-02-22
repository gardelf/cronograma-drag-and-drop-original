from openai import OpenAI
from config import get_config

config = get_config()
api_key = config['OPENAI_API_KEY']

print(f"Testing OpenAI API Key...")
print(f"Key starts with: {api_key[:20]}...")
print(f"Key length: {len(api_key)}")

try:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'API Key works!' if you can read this."}
        ],
        max_tokens=20
    )
    
    print(f"\n✅ SUCCESS! OpenAI API is working!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\nFull error details:")
    import traceback
    traceback.print_exc()
