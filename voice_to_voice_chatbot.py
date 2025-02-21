import gradio as gr
import whisper
import os
import requests
from gtts import gTTS

# Initialize Whisper Model
model = whisper.load_model("base")

def transcribe_audio(audio_path):
    """Converts speech to text using Whisper"""
    result = model.transcribe(audio_path)
    return result["text"]

def fetch_response_from_backend(text, chat_history):
    """Sends user query and chat history to Flask backend for a response."""
    try:
        payload = {"query": text, "chat_history": chat_history}  # Full conversation context
        response = requests.post("http://127.0.0.1:5000/query", json=payload)
        return response.json().get("response", "No response found.")
    except Exception as e:
        print("❌ Backend request failed:", e)
        return "Backend not available."

def text_to_speech(text):
    """Converts AI text response into speech."""
    tts = gTTS(text)
    output_path = "response.mp3"
    tts.save(output_path)
    return output_path

def process_voice(audio_path, chat_history):
    """Handles voice input, detects intent, fetches response, and returns audio."""
    if not audio_path:
        return chat_history, None, None  

    user_text = transcribe_audio(audio_path)
    ai_text = fetch_response_from_backend(user_text, chat_history)  # Intent recognition handled in backend
    ai_audio = text_to_speech(ai_text)

    chat_history.append((user_text, ai_text))  
    return chat_history, ai_audio, None  

# Gradio UI
with gr.Blocks(css="""
    .gradio-container {background-color: #0a0a0a; color: white; text-align: center;}
    .gr-chatbot {border-radius: 15px; border: none; background: #111; width: 80%; margin: auto;}
    .gr-audio {border-radius: 10px; width: 50%; margin: auto;}
""") as demo:

    gr.Markdown("<h1 style='text-align: center;'>🗣️ Voice-to-Voice AI Chatbot</h1>")
    chat_history = gr.Chatbot(height=450, bubble_full_width=False, avatar_images=(None, "https://i.imgur.com/Q7ZdWjl.png"))

    mic_input = gr.Audio(sources=["microphone"], type="filepath", label="🎤 Speak now", interactive=True)
    response_audio = gr.Audio(interactive=False, autoplay=True, visible=True)

    mic_input.change(process_voice, inputs=[mic_input, chat_history], outputs=[chat_history, response_audio, mic_input])

demo.launch()
