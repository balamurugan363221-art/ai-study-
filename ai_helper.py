"""ai_helper.py – External AI handler using Groq"""
from groq import Groq

# 🚨 HARDCODED API KEY 🚨
# Paste your real key inside these quotes. Make sure there are NO spaces!
API_KEY = "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"

# Initialize the Groq client directly with the key
client = Groq(api_key=API_KEY)

# The open-source model we are using
MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"

def get_ai_response(prompt: str, language: str = "English") -> str:
    # Quick check to remind you if the key hasn't been pasted yet
    if not API_KEY or API_KEY == "gsk_paste_your_actual_key_here":
        return "⚠️ AI Error: Please paste your real Groq API key into ai_helper.py."

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
            temperature=0.4, # Lowered for more accurate, factual answers
            max_tokens=2048, # Increased to allow room for larger diagrams
        )
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f"⚠️ AI error: {str(e)}"