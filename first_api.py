# import os
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# # Configure the client for OpenRouter
# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.getenv("OPENAI_KEY"),  # Note: Ensure this matches your .env file variable name
# )

# def ask_ai(question):
#     stream = client.chat.completions.create(
#         model="openrouter/free",
#         messages=[
#             {"role": "system", "content": "You are a good tutor"},
#             {"role": "user", "content": question}
#         ],
#         stream= True
#     )
#     # FIX: This line must be indented exactly 4 spaces (matching the response variable line)
#     for chunk in stream:
#         content= chunk.choices[0].delta.content
#         if content:
#             print(content, end='', flush= True)

# while True:
#     question = input("Ask: ")
#     if question.lower() in ['exit', 'quit']:
#         break
#     print(ask_ai(question))
#     print('-' * 20)




import os
import time
from openai import OpenAI
from dotenv import load_dotenv
import openai

load_dotenv()

# Configure the client for OpenRouter
client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.getenv("MISTRAL_API_KEY"),  
    timeout= 60
)

def ask_ai(question):
    for attempt in range(3):
        try:
            stream = client.chat.completions.create(
                model="mistral-medium-3.5",
                messages=[
                    {"role": "system", "content": "You are a good tutor"},
                    {"role": "user", "content": question}
                ],
                stream= True
            )
           
            for chunk in stream:
                content= chunk.choices[0].delta.content
                if content:
                    print(content, end='', flush= True)
        except openai.APITimeoutError:
            print(f'Timeout on attempt {attempt + 1}. Retrying in 3 seconds...')
            time.sleep(3)
    raise 'Failed to get response after multiple attempts due to timeouts'

while True:
    question = input("Ask: ")
    if question.lower() in ['exit', 'quit']:
        break
    print(ask_ai(question))
    print('-' * 20)




