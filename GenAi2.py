# GenAI Powered Virtual Assistant (Professional ChatGPT Style Clone)
import streamlit as st
import requests
import datetime
import pyttsx3
import speech_recognition as sr
import threading
import time
import json
import pyperclip
import base64
from io import StringIO

# ===== CONFIGURATION =====
OPENROUTER_API_KEY = "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"
MODEL_NAME = "mistralai/mistral-7b-instruct"

# ===== SETUP =====
st.set_page_config(
    page_title="SmartAI Assistant", 
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Initialize TTS engine with Windows PowerShell fallback
import subprocess

def speak_windows(text):
    """Use Windows built-in speech directly with voice selection"""
    try:
        # Kill any existing PowerShell speech processes first
        subprocess.run("taskkill /f /im powershell.exe", shell=True, capture_output=True)
        import time
        time.sleep(0.1)  # Brief pause

        # Use specific voice names that are commonly available on Windows
        if st.session_state.voice_gender == "Female":
            # Try common female voice names
            cmd = f'''powershell -Command "
            Add-Type -AssemblyName System.Speech;
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            try {{
                $speak.SelectVoice('Microsoft Zira Desktop');
            }} catch {{
                try {{
                    $speak.SelectVoice('Microsoft Hazel Desktop');
                }} catch {{
                    try {{
                        $speak.SelectVoice('Microsoft Eva Desktop');
                    }} catch {{
                        # Use any available female voice
                        $voices = $speak.GetInstalledVoices();
                        foreach($voice in $voices) {{
                            if($voice.VoiceInfo.Gender -eq 'Female') {{
                                $speak.SelectVoice($voice.VoiceInfo.Name);
                                break;
                            }}
                        }}
                    }}
                }}
            }}
            $speak.Speak('{text}');"'''
        else:
            # Try common male voice names
            cmd = f'''powershell -Command "
            Add-Type -AssemblyName System.Speech;
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            try {{
                $speak.SelectVoice('Microsoft David Desktop');
            }} catch {{
                try {{
                    $speak.SelectVoice('Microsoft Mark Desktop');
                }} catch {{
                    try {{
                        $speak.SelectVoice('Microsoft Richard Desktop');
                    }} catch {{
                        # Use any available male voice
                        $voices = $speak.GetInstalledVoices();
                        foreach($voice in $voices) {{
                            if($voice.VoiceInfo.Gender -eq 'Male') {{
                                $speak.SelectVoice($voice.VoiceInfo.Name);
                                break;
                            }}
                        }}
                    }}
                }}
            }}
            $speak.Speak('{text}');"'''

        subprocess.run(cmd, shell=True, capture_output=True)
        return True
    except Exception as e:
        print(f"Windows speech error: {e}")
        # Fallback to basic speech without voice selection
        try:
            cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{text}\')"'
            subprocess.run(cmd, shell=True, capture_output=True)
            return True
        except:
            return False

# Initialize TTS - Use Windows speech primarily for better voice control
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    voice_ids = {
        "Male": voices[0].id if voices else None,
        "Female": voices[1].id if len(voices) > 1 else (voices[0].id if voices else None)
    }
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)
    TTS_AVAILABLE = True
    USE_PYTTSX3 = False  # Prefer Windows speech for better voice selection
except Exception as e:
    engine = None
    voice_ids = {"Male": None, "Female": None}
    TTS_AVAILABLE = True
    USE_PYTTSX3 = False

# Initialize speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

# ===== SESSION STATE DEFAULTS =====
for key, default in {
    "history": [],
    "author": "",
    "voice_output": False,
    "theme": "Light Mode",
    "speaking": False,
    "input_text": "",
    "voice_gender": "Male",
    "auto_speak": False,
    "conversation_count": 0,
    "last_response": "",
    "typing_effect": True,
    "show_timestamps": True,
    "export_format": "TXT",
    "current_speech": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ===== THEME STYLES =====
def get_theme_css(theme):
    themes = {
        "Light Mode": """
            <style>
            .main-header { color: #1f77b4; text-align: center; margin-bottom: 2rem; }
            .chat-container { background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
            .user-message { background: #e3f2fd; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .assistant-message { background: #f1f8e9; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .timestamp { font-size: 0.8rem; color: #666; margin-top: 0.5rem; }
            .stButton > button { height: 2.5rem; font-size: 1.1rem; }
            </style>
        """,
        "Dark Mode": """
            <style>
            .main-header { color: #64b5f6; text-align: center; margin-bottom: 2rem; }
            .chat-container { background: #2e2e2e; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
            .user-message { background: #1565c0; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .assistant-message { background: #2e7d32; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .timestamp { font-size: 0.8rem; color: #bbb; margin-top: 0.5rem; }
            .stButton > button { height: 2.5rem; font-size: 1.1rem; }
            </style>
        """,
        "Cyberpunk": """
            <style>
            .main-header { color: #ff00ff; text-align: center; margin-bottom: 2rem; text-shadow: 0 0 10px #ff00ff; }
            .chat-container { background: #0a0a0a; border: 1px solid #00ffff; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
            .user-message { background: #1a0033; border: 1px solid #ff00ff; color: #ff00ff; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .assistant-message { background: #001a33; border: 1px solid #00ffff; color: #00ffff; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .timestamp { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }
            .stButton > button { height: 2.5rem; font-size: 1.1rem; }
            </style>
        """,
        "Ocean Blue": """
            <style>
            .main-header { color: #0277bd; text-align: center; margin-bottom: 2rem; }
            .chat-container { background: #e1f5fe; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
            .user-message { background: #01579b; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .assistant-message { background: #0288d1; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .timestamp { font-size: 0.8rem; color: #666; margin-top: 0.5rem; }
            .stButton > button { height: 2.5rem; font-size: 1.1rem; }
            </style>
        """,
        "Emerald": """
            <style>
            .main-header { color: #00695c; text-align: center; margin-bottom: 2rem; }
            .chat-container { background: #e0f2f1; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
            .user-message { background: #004d40; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .assistant-message { background: #00796b; color: white; padding: 1rem; border-radius: 15px; margin: 0.5rem 0; }
            .timestamp { font-size: 0.8rem; color: #666; margin-top: 0.5rem; }
            .stButton > button { height: 2.5rem; font-size: 1.1rem; }
            </style>
        """
    }
    return themes.get(theme, themes["Light Mode"])

# ===== VOICE HANDLING =====
def set_voice(voice_name):
    if engine and voice_ids.get(voice_name):
        engine.setProperty('voice', voice_ids[voice_name])

def speak(text):
    """Start speaking text with proper voice selection"""
    def _speak():
        try:
            # Use Windows speech directly for better voice control
            speak_windows(text)
        except Exception as e:
            print(f"Speech error: {e}")
        finally:
            st.session_state.speaking = False
            st.session_state.current_speech = ""

    # Only start if not already speaking
    if not st.session_state.speaking:
        st.session_state.speaking = True
        st.session_state.current_speech = text
        threading.Thread(target=_speak, daemon=True).start()
        st.success(f"🔊 Speaking in {st.session_state.voice_gender} voice...")

def toggle_speak(text):
    """Toggle speech on/off for specific text"""
    if st.session_state.speaking and st.session_state.get('current_speech', '') == text:
        # If currently speaking this exact text, stop it
        stop_speaking()
    elif not st.session_state.speaking:
        # Only start if not already speaking anything
        speak(text)

def stop_speaking():
    """Stop all speech immediately"""
    try:
        # Stop pyttsx3 if running
        if USE_PYTTSX3 and engine:
            engine.stop()

        # Stop Windows speech by killing PowerShell processes
        subprocess.run("taskkill /f /im powershell.exe", shell=True, capture_output=True)

        st.session_state.speaking = False
        st.session_state.current_speech = ""

    except Exception as e:
        print(f"Stop speech error: {e}")
        st.session_state.speaking = False
        st.session_state.current_speech = ""

def listen():
    try:
        with sr.Microphone() as source:
            st.toast("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, phrase_time_limit=8, timeout=2)
        
        st.toast("🔄 Processing speech...")
        text = recognizer.recognize_google(audio)
        st.session_state.input_text = text
        st.success(f"🎤 Heard: {text}")
        return text
    except sr.WaitTimeoutError:
        st.warning("⏰ No speech detected. Please try again.")
        return ""
    except sr.UnknownValueError:
        st.warning("🤷 Could not understand audio. Please speak clearly.")
        return ""
    except Exception as e:
        st.error(f"🎤 Speech recognition error: {e}")
        return ""

# ===== OPENROUTER API CALL =====
def ask_openrouter(prompt):
    messages = [{"role": "system", "content": "You are a helpful, professional AI assistant. Provide accurate, detailed, and helpful responses."}]
    
    # Add conversation history
    for pair in st.session_state.history:
        messages.append({"role": "user", "content": pair["user"]})
        messages.append({"role": "assistant", "content": pair["assistant"]})
    
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        with st.spinner("🤖 AI is thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                headers=headers, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()['choices'][0]['message']['content'].strip()
            st.session_state.last_response = result
            return result
    except requests.exceptions.Timeout:
        return "⏰ Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"🌐 Network error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def handle_command(text):
    text_lower = text.lower()
    
    # Built-in commands
    if any(word in text_lower for word in ["time", "what time"]):
        return f"⏰ Current time: {datetime.datetime.now().strftime('%I:%M %p')}"
    
    if any(word in text_lower for word in ["date", "today", "what date"]):
        return f"📅 Today's date: {datetime.datetime.now().strftime('%A, %B %d, %Y')}"
    
    if any(word in text_lower for word in ["weather", "temperature"]):
        return "🌤️ I don't have access to real-time weather data, but you can check your local weather app or website for current conditions."
    
    # Default to AI response
    return ask_openrouter(text)

# ===== UTILITY FUNCTIONS =====
def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        st.success("📋 Copied to clipboard!")
    except Exception as e:
        st.error(f"Copy failed: {e}")

def export_chat(format_type="TXT"):
    if not st.session_state.history:
        st.warning("No chat history to export.")
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "TXT":
        content = f"GenAI Assistant Chat Export\nDate: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Author: {st.session_state.author or 'Anonymous'}\n"
        content += "=" * 50 + "\n\n"
        
        for i, msg in enumerate(st.session_state.history, 1):
            content += f"[{i}] You: {msg['user']}\n"
            content += f"[{i}] Assistant: {msg['assistant']}\n\n"
        
        return content, f"chat_export_{timestamp}.txt"
    
    elif format_type == "JSON":
        data = {
            "export_info": {
                "timestamp": datetime.datetime.now().isoformat(),
                "author": st.session_state.author or "Anonymous",
                "total_messages": len(st.session_state.history)
            },
            "conversation": st.session_state.history
        }
        content = json.dumps(data, indent=2)
        return content, f"chat_export_{timestamp}.json"

def get_conversation_stats():
    if not st.session_state.history:
        return "No conversation data available."

    total_messages = len(st.session_state.history)
    user_words = sum(len(msg["user"].split()) for msg in st.session_state.history)
    assistant_words = sum(len(msg["assistant"].split()) for msg in st.session_state.history)

    return f"""
    📊 **Conversation Statistics:**
    - Total exchanges: {total_messages}
    - Your words: {user_words:,}
    - Assistant words: {assistant_words:,}
    - Total words: {user_words + assistant_words:,}
    """

# ===== MAIN APPLICATION =====
def main():
    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("# 🧠 SmartAI Assistant")
        st.markdown("---")

        # User Settings
        st.markdown("### 👤 User Settings")
        st.session_state.author = st.text_input(
            "Your Name",
            st.session_state.author,
            placeholder="Enter your name..."
        )

        # Theme Selection
        st.markdown("### 🎨 Appearance")
        st.session_state.theme = st.selectbox(
            "Theme",
            ["Light Mode", "Dark Mode", "Cyberpunk", "Ocean Blue", "Emerald"],
            index=["Light Mode", "Dark Mode", "Cyberpunk", "Ocean Blue", "Emerald"].index(st.session_state.theme)
        )

        # Voice Settings
        st.markdown("### 🎙️ Voice Settings")
        st.session_state.voice_gender = st.selectbox(
            "Voice Gender",
            ["Male"],
            index=0
        )

        st.session_state.auto_speak = st.checkbox(
            "🔊 Auto-speak responses",
            st.session_state.auto_speak
        )

        st.session_state.show_timestamps = st.checkbox(
            "⏰ Show timestamps",
            st.session_state.show_timestamps
        )

        # TTS Test
        test_label = "⏹️ Stop Voice" if st.session_state.speaking else "🔊 Test Voice"
        if st.button(test_label, use_container_width=True):
            toggle_speak(f"Hello! This is a {st.session_state.voice_gender.lower()} voice test!")

        # Voice debug button
        if st.button("🔍 Check Voices", use_container_width=True):
            try:
                cmd = '''powershell -Command "
                Add-Type -AssemblyName System.Speech;
                $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
                $voices = $speak.GetInstalledVoices();
                foreach($voice in $voices) {
                    Write-Host ($voice.VoiceInfo.Name + ' - ' + $voice.VoiceInfo.Gender);
                }"'''
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                st.text("Available voices:")
                st.text(result.stdout)
            except Exception as e:
                st.error(f"Error checking voices: {e}")

        # Chat Controls
        st.markdown("### 💬 Chat Controls")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New Chat", use_container_width=True):
                st.session_state.history.clear()
                st.session_state.conversation_count = 0
                st.success("Chat cleared!")
                st.rerun()

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Export Options
        st.markdown("### 📁 Export & Tools")
        st.session_state.export_format = st.selectbox(
            "Export Format",
            ["TXT", "JSON"],
            index=0 if st.session_state.export_format == "TXT" else 1
        )

        if st.button("💾 Export Chat", use_container_width=True):
            if st.session_state.history:
                content, filename = export_chat(st.session_state.export_format)
                st.download_button(
                    f"📥 Download {st.session_state.export_format}",
                    content,
                    file_name=filename,
                    mime="text/plain" if st.session_state.export_format == "TXT" else "application/json",
                    use_container_width=True
                )
            else:
                st.warning("No chat to export!")

        if st.button("📋 Copy Last Response", use_container_width=True):
            if st.session_state.last_response:
                copy_to_clipboard(st.session_state.last_response)
            else:
                st.warning("No response to copy!")

        # Statistics
        st.markdown("### 📊 Statistics")
        if st.button("📈 Show Stats", use_container_width=True):
            st.markdown(get_conversation_stats())

        # Speaking Status
        if st.session_state.speaking:
            st.markdown("### 🔊 Status")
            st.info("🗣️ Currently speaking...")

    # ===== MAIN CONTENT =====
    st.markdown('<h1 class="main-header"> 🤖 SmartAI Virtual Assistant </h1>', unsafe_allow_html=True)

    # Welcome message and user info
    if st.session_state.author:
        st.markdown(f"**👋 Welcome, {st.session_state.author}!**")
    else:
        st.info("👤 Please enter your name in the sidebar to personalize your experience.")

    # Display conversation count
    if st.session_state.history:
        st.markdown(f"**💬 Conversation: {len(st.session_state.history)} exchanges**")

    # Chat History Display
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.history):
            # User message
            with st.chat_message("user", avatar="👤"):
                st.markdown(f'<div class="user-message">{msg["user"]}</div>', unsafe_allow_html=True)
                if st.session_state.show_timestamps:
                    st.markdown(f'<div class="timestamp">Sent at: {datetime.datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

            # Assistant message
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f'<div class="assistant-message">{msg["assistant"]}</div>', unsafe_allow_html=True)
                if st.session_state.show_timestamps:
                    st.markdown(f'<div class="timestamp">Replied at: {datetime.datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

                # Individual message controls
                col1, col2, _ = st.columns([1, 1, 8])
                with col1:
                    # Show stop icon only if currently speaking THIS specific message
                    is_speaking_this = (st.session_state.speaking and
                                      st.session_state.current_speech == msg["assistant"])
                    speak_icon = "⏹️" if is_speaking_this else "🔊"
                    speak_help = "Stop speaking" if is_speaking_this else "Speak this response"

                    if st.button(speak_icon, key=f"speak_{i}", help=speak_help):
                        toggle_speak(msg["assistant"])
                with col2:
                    if st.button("📋", key=f"copy_{i}", help="Copy this response"):
                        copy_to_clipboard(msg["assistant"])

    # ===== INPUT SECTION =====
    st.markdown("---")

    # Input row with perfectly aligned buttons
    col_input, col_buttons = st.columns([85, 15])

    with col_input:
        user_input = st.text_area(
            label="",
            key="message_input",
            placeholder="💭 Type your message here... (or use voice input)",
            label_visibility="collapsed",
            value=st.session_state.input_text,
            height=80
        )

    with col_buttons:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        btn_cols = st.columns(2)
        with btn_cols[0]:
            mic_clicked = st.button("🎤", help="Voice input", use_container_width=True, key="mic_btn")
        with btn_cols[1]:
            send_clicked = st.button("➡️", help="Send message", use_container_width=True, key="send_btn")

    # Handle button actions
    if mic_clicked:
        with st.spinner("🎤 Listening..."):
            captured_text = listen()
            if captured_text:
                st.session_state.input_text = captured_text
                st.rerun()

    if send_clicked and user_input.strip():
        # Add user message to history
        st.session_state.history.append({"user": user_input, "assistant": "..."})
        st.session_state.conversation_count += 1

        # Get AI response
        with st.spinner("🤖 Generating response..."):
            response = handle_command(user_input)
            st.session_state.history[-1]["assistant"] = response
            st.session_state.last_response = response

        # Auto-speak if enabled
        if st.session_state.auto_speak:
            speak(response)

        # Clear input and refresh
        st.session_state.input_text = ""
        st.rerun()

    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    quick_cols = st.columns(4)

    with quick_cols[0]:
        if st.button("❓ Ask about time", use_container_width=True):
            st.session_state.input_text = "What time is it?"
            st.rerun()

    with quick_cols[1]:
        if st.button("📅 Ask about date", use_container_width=True):
            st.session_state.input_text = "What's today's date?"
            st.rerun()

    with quick_cols[2]:
        if st.button("💡 Get a tip", use_container_width=True):
            st.session_state.input_text = "Give me a useful productivity tip"
            st.rerun()

    with quick_cols[3]:
        if st.button("🎲 Random fact", use_container_width=True):
            st.session_state.input_text = "Tell me an interesting random fact"
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)  # Add extra space
    st.markdown(
    """
        <div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 2rem; padding: 1rem;'>
        © 2025 SmartAI Virtual Assistant | Developed by Munesula Vamshi<br>
        </div>
    """,
    unsafe_allow_html=True
)

if __name__ == "__main__":
    main()
