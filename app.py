import os
import re
from flask import Flask, request, Response, render_template_string
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.ai.inference.models import SystemMessage, UserMessage

# Load environment variables
load_dotenv()
model_name = os.getenv("DEPLOYMENT_NAME")
app = Flask(__name__)

# Initialize the ChatCompletionsClient
client = ChatCompletionsClient(
    endpoint=os.environ["AZURE_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_KEY"]),
)

@app.route('/')
def home():
    return render_template_string(r'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat Stream</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                #chat { max-width: 800px; margin: auto; }
                #messages { height: 400px; border: 1px solid #ccc; padding: 10px; overflow-y: auto; margin-bottom: 10px; }
                .message { margin: 5px 0; padding: 5px; border-radius: 5px; }
                .user { background-color: #e3f2fd; }
                .assistant-thinking { background-color: #fff9c4; font-style: italic; }
                .assistant { background-color: #f5f5f5; }
                #input { width: calc(100% - 80px); padding: 8px; }
                button { width: 70px; padding: 8px; }
                h1 { text-align: center; color: #333; }
            </style>
        </head>
        <body>
            <h1>UoB Postgraduate Assistant</h1>
            <div id="chat">
                <div id="messages"></div>
                <form onsubmit="sendMessage(event)">
                    <input type="text" id="input" placeholder="Type your message...">
                    <button type="submit">Send</button>
                </form>
            </div>
            <script>
                async function sendMessage(event) {
                    event.preventDefault();
                    const input = document.getElementById('input');
                    const userMsg = input.value;
                    input.value = '';
                    appendMessage("You: " + userMsg, "user");

                    try {
                        const response = await fetch('/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: userMsg })
                        });

                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        let buffer = "";
                        let thinkingContent = "";
                        let responseContent = "";
                        let thinkingDisplayed = false;
                        let responseMessageElement = null;

                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;

                            const chunk = decoder.decode(value, { stream: true });
                            buffer += chunk;

                            if (!thinkingDisplayed && buffer.includes("<think>")) {
                                const thinkEndIndex = buffer.indexOf("</think>");
                                if (thinkEndIndex !== -1) {
                                    thinkingContent = buffer.substring(
                                        buffer.indexOf("<think>") + "<think>".length,
                                        thinkEndIndex
                                    ).trim();
                                    appendMessage("Assistant Thinking: " + thinkingContent, "assistant-thinking");
                                    buffer = buffer.substring(thinkEndIndex + "</think>".length);
                                    thinkingDisplayed = true;
                                }
                            }

                            if (thinkingDisplayed || !buffer.includes("<think>")) {
                                responseContent += buffer;
                                buffer = "";

                                if (responseContent.trim()) {
                                    if (!responseMessageElement) {
                                        responseMessageElement = document.createElement('div');
                                        responseMessageElement.className = 'message assistant';
                                        document.getElementById('messages').appendChild(responseMessageElement);
                                    }
                                    responseMessageElement.textContent = "Assistant: " + responseContent;
                                }
                            }
                        }

                        if (buffer.trim()) {
                            if (!responseMessageElement) {
                                responseMessageElement = document.createElement('div');
                                responseMessageElement.className = 'message assistant';
                                document.getElementById('messages').appendChild(responseMessageElement);
                            }
                            responseMessageElement.textContent = "Assistant: " + (responseContent + buffer);
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        appendMessage("Assistant: Failed to get response", "assistant");
                    }
                }

                function appendMessage(content, className) {
                    const messagesDiv = document.getElementById('messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ' + className;
                    messageDiv.textContent = content;
                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
            </script>
        </body>
        </html>
    ''')

uob_info = "Why Choose Birmingham : Recognized as one of the most targeted universities by top employers.  Offers strong career support, ensuring students are well-prepared for employment.  Emphasizes student well-being, personal development, and a vibrant research culture. Programmes and Study Options : Flexible study options include full-time, part-time, distance learning, and microcredentials.  Courses span various disciplines with tailored options for diverse career aspirations. Application Process : The prospectus explains steps from finding a course to applying online, meeting conditions, and confirming an offer.  Detailed guidance on entry requirements, English language qualifications, and document submission is provided. Funding and Scholarships  Information on UK and international scholarships, tuition fee details, and funding options such as postgraduate loans. Career Support  Dedicated career guidance, networking events, employer connections, and mentoring are available.  Alumni insights and success stories showcase career outcomes across industries. Campus Life  The campus features modern facilities, study spaces, and a rich social environment.  Various accommodation options are available both on and off-campus. Living in Birmingham  Describes the vibrant city life, cultural opportunities, and student-friendly neighborhoods. Support Services  Includes mental health resources, disability support, and a multi-faith chaplaincy for well-being.  The Student Guild offers representation, social activities, and volunteer opportunities. Entrepreneurship and Innovation  Highlights initiatives like the Elevate program, which supports student startups. The document effectively portrays Birmingham as a prestigious university offering comprehensive academic, career, and personal development support for postgraduate students."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']

    messages = [
        SystemMessage(content="You are a helpful assistant that provides information about postgraduate studies at the University of Birmingham." + uob_info),
        UserMessage(content=user_message),
    ]

    model = model_name  # Corrected model assignment (removed trailing comma)

    # Include `model` parameter in `client.complete()`
    stream = client.complete(messages=messages, model=model, stream=True)

    def generate():
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)