"""ai_helper.py – External AI handler using Groq"""
import os
from dotenv import load_dotenv
from groq import Groq

# 1. Load environment variables securely
load_dotenv(override=True)

# 2. Fetch the API key from the environment
API_KEY = os.environ.get("GROQ_API_KEY")

# 3. Initialize the Groq client only if the key exists
client = Groq(api_key=API_KEY) if API_KEY else None

MODEL_NAME = "llama3-8b-8192"

def get_ai_response(prompt: str, language: str = "English") -> str:
    # Quick check to ensure the key loaded properly
    if not client:
        return "⚠️ AI Error: GROQ_API_KEY is missing from the environment variables."

    # The System Prompt: Professional tutor that draws diagrams
    dynamic_system_prompt = (
        f"You are AI Study Buddy, a helpful, knowledgeable, and friendly academic assistant. "
        f"Answer the user's questions clearly, naturally, and accurately. "
        f"CRITICAL INSTRUCTION: If a visual diagram, flowchart, or architecture map would help explain the concept, you MUST generate a Mermaid.js diagram. "
        f"Enclose all Mermaid diagram code inside a ```mermaid code block. "
        f"IMPORTANT: You MUST translate your thoughts and provide your final text answer ONLY in {language}."
    )

    try:
        # Send the prompt to Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=MODEL_NAME,
            temperature=0.4, 
            max_tokens=2048, 
        )
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f"⚠️ AI error: {str(e)}"