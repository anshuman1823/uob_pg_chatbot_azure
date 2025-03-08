import os
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.ai.inference.models import SystemMessage, UserMessage

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")
model_name = os.getenv("DEPLOYMENT_NAME")

client = ChatCompletionsClient(
    endpoint=os.environ["AZURE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_KEY"]),
)

response = client.complete(
    messages=[
        SystemMessage(content="You are an AI assistant that helps people find information regarding postgraduate studies at University of Birmingham."),
        UserMessage(content="Tell me about the programs available"),
    ],
    model = model_name,
)

print("Response:", response.choices[0].message.content)
