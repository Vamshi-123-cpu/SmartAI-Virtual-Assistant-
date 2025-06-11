# GenAI Powered Virtual Assistant (Cloud-Compatible with All Features)
import streamlit as st
import requests
import datetime
import threading
import time
import json
import base64
from io import StringIO

# ===== CONFIGURATION =====
OPENROUTER_API_KEY = "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"
MODEL_NAME = "mistralai/mistral-7b-instruct"

# ===== SETUP =====
st.set_page_config(
    page_title="GenAI Virtual Assistant", 
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="collapsed"
)

# ===== BROWSER-BASED VOICE FUNCTIONS =====
def speak_browser(text):
    """Use browser's built-in speech synthesis"""
    # Clean text for JavaScript
    clean_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
    
    st.markdown(f"""
        <script>
        function speakText() {{
            if ('speechSynthesis' in window) {{
                // Stop any ongoing speech
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(`{clean_text}`);
                utterance.rate = 0.8;
                utterance.pitch = 1;
                utterance.volume = 1;
                
                // Set voice based on gender preference
                const voices = window.speechSynthesis.getVoices();
                const genderPref = '{st.session_state.get("voice_gender", "Male")}';
                
                if (genderPref === 'Female') {{
                    const femaleVoice = voices.find(voice => voice.name.toLowerCase().includes('female') || voice.name.toLowerCase().includes('zira') || voice.name.toLowerCase().includes('susan'));
                    if (femaleVoice) utterance.voice = femaleVoice;
                }} else {{
                    const maleVoice = voices.find(voice => voice.name.toLowerCase().includes('male') || voice.name.toLowerCase().includes('david') || voice.name.toLowerCase().includes('mark'));
                    if (maleVoice) utterance.voice = maleVoice;
                }}
                
                utterance.onstart = function() {{
                    console.log('Speech started');
                }};
                
                utterance.onend = function() {{
                    console.log('Speech ended');
                }};
                
                window.speechSynthesis.speak(utterance);
            }} else {{
                alert('Speech synthesis not supported in this browser');
            }}
        }}
        
        // Auto-execute
        speakText();
        </script>
    """, unsafe_allow_html=True)

def stop_speaking_browser():
    """Stop browser speech synthesis"""
    st.markdown("""
        <script>
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        </script>
    """, unsafe_allow_html=True)

def listen_browser():
    """Use browser's speech recognition"""
    st.markdown("""
        <div style='padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 15px; margin: 1rem 0; color: white; text-align: center;'>
            <h4 style='margin: 0 0 1rem 0;'>🎤 Voice Input</h4>
            <button onclick="startVoiceRecognition()" 
                    style='padding: 0.8rem 2rem; background: white; color: #667eea; 
                           border: none; border-radius: 25px; cursor: pointer; font-weight: bold;
                           font-size: 1rem; transition: all 0.3s ease;'
                    onmouseover='this.style.transform="scale(1.05)"'
                    onmouseout='this.style.transform="scale(1)"'>
                🎤 Click to Speak
            </button>
            <div id="voiceResult" style='margin-top: 1rem; font-weight: bold; min-height: 2rem;'></div>
        </div>
        
        <script>
        function startVoiceRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                
                recognition.onstart = function() {
                    document.getElementById('voiceResult').innerHTML = '🎤 Listening... Speak now!';
                };
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('voiceResult').innerHTML = '✅ You said: "' + transcript + '"';
                    
                    // Set the input value
                    setTimeout(function() {
                        const textArea = document.querySelector('textarea[data-testid="textArea-input"]');
                        if (textArea) {
                            textArea.value = transcript;
                            textArea.dispatchEvent(new Event('input', { bubbles: true }));
                            textArea.focus();
                        }
                    }, 500);
                };
                
                recognition.onerror = function(event) {
                    document.getElementById('voiceResult').innerHTML = '❌ Error: ' + event.error + '. Please try again.';
                };
                
                recognition.onend = function() {
                    console.log('Speech recognition ended');
                };
                
                recognition.start();
            } else {
                document.getElementById('voiceResult').innerHTML = '❌ Speech recognition not supported in this browser. Try Chrome or Edge.';
            }
        }
        
        // Load voices when page loads
        if ('speechSynthesis' in window) {
            window.speechSynthesis.getVoices();
        }
        </script>
    """, unsafe_allow_html=True)

def copy_to_clipboard_browser(text):
    """Use browser's clipboard API"""
    # Clean text for JavaScript
    clean_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
    
    st.markdown(f"""
        <script>
        function copyToClipboard() {{
            const text = `{clean_text}`;
            
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(function() {{
                    console.log('Text copied to clipboard successfully');
                }}).catch(function(err) {{
                    console.error('Failed to copy text: ', err);
                    // Fallback method
                    fallbackCopy(text);
                }});
            }} else {{
                // Fallback for older browsers
                fallbackCopy(text);
            }}
        }}
        
        function fallbackCopy(text) {{
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
                console.log('Fallback copy successful');
            }} catch (err) {{
                console.error('Fallback copy failed: ', err);
            }}
            
            document.body.removeChild(textArea);
        }}
        
        // Auto-execute
        copyToClipboard();
        </script>
    """, unsafe_allow_html=True)

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

# ===== MODERN PROFESSIONAL STYLES =====
def get_theme_css(theme):
    base_css = """
        <style>
        /* Hide Streamlit elements for clean interface */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Modern app container */
        .main .block-container {
            padding: 0;
            max-width: 100%;
            background: #ffffff;
        }
        
        /* Professional header */
        .app-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem 2rem;
            color: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: -1rem -1rem 2rem -1rem;
        }
        
        .app-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .app-subtitle {
            font-size: 1rem;
            opacity: 0.9;
            margin: 0.5rem 0 0 0;
        }
        
        /* Modern message styling */
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 18px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            border-bottom-right-radius: 6px;
        }
        
        .assistant-message {
            background: #f8f9fa;
            color: #333;
            padding: 1rem 1.5rem;
            border-radius: 18px;
            margin: 1rem 0;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-bottom-left-radius: 6px;
        }
        
        /* Professional buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* Modern text area */
        .stTextArea > div > div > textarea {
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 1rem 1.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #f8f9fa;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: white;
        }
        
        /* Quick action cards */
        .quick-action-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .quick-action-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .quick-action-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        .quick-action-text {
            font-weight: 600;
            color: #333;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .app-header {
                padding: 1rem;
            }
            
            .app-title {
                font-size: 1.8rem;
            }
        }
        </style>
    """
    return base_css

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
    # Apply modern CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    # Professional Header
    st.markdown(f"""
        <div class="app-header">
            <h1 class="app-title">🤖 GenAI Virtual Assistant</h1>
            <p class="app-subtitle">Professional AI Assistant with Advanced Voice Capabilities</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                {f"Welcome, {st.session_state.author}!" if st.session_state.author else "Welcome, Guest!"} |
                {st.session_state.theme} |
                {len(st.session_state.history)} conversations
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        st.session_state.author = st.text_input(
            "👤 Your Name",
            st.session_state.author,
            placeholder="Enter your name..."
        )

        st.session_state.theme = st.selectbox(
            "🎨 Theme",
            ["Light Mode", "Dark Mode", "Cyberpunk", "Ocean Blue", "Emerald"],
            index=["Light Mode", "Dark Mode", "Cyberpunk", "Ocean Blue", "Emerald"].index(st.session_state.theme)
        )

        st.session_state.voice_gender = st.selectbox(
            "🎙️ Voice Gender",
            ["Male", "Female"],
            index=0 if st.session_state.voice_gender == "Male" else 1
        )

        st.session_state.auto_speak = st.checkbox(
            "🔊 Auto-speak responses",
            st.session_state.auto_speak
        )

        st.session_state.show_timestamps = st.checkbox(
            "⏰ Show timestamps",
            st.session_state.show_timestamps
        )

        st.markdown("---")

        # Voice Test
        if st.button("🔊 Test Voice", use_container_width=True):
            speak_browser("Hello! This is a voice test. The browser-based voice system is working perfectly!")
            st.success("🔊 Voice test activated!")

        # Chat Controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New", use_container_width=True):
                st.session_state.history.clear()
                st.session_state.conversation_count = 0
                st.success("✅ New chat started!")
                st.rerun()

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Export Options
        st.markdown("### 📁 Export")
        st.session_state.export_format = st.selectbox(
            "Format",
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
                copy_to_clipboard_browser(st.session_state.last_response)
                st.success("📋 Copied!")
            else:
                st.warning("No response to copy!")

        # Statistics
        if st.button("📊 Show Stats", use_container_width=True):
            st.markdown(get_conversation_stats())

    # Main Chat Area
    if not st.session_state.history:
        # Welcome screen
        st.markdown("""
            <div style='text-align: center; padding: 3rem 1rem;'>
                <h2 style='color: #667eea; margin-bottom: 1rem;'>Welcome to Your AI Assistant!</h2>
                <p style='font-size: 1.1rem; color: #666; margin-bottom: 2rem;'>
                    Start a conversation below or try voice input. All features work in your browser!
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Feature showcase
        st.markdown("### ✨ Features Available")
        cols = st.columns(4)

        with cols[0]:
            st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">🤖</div>
                    <div class="quick-action-text">AI Chat</div>
                </div>
            """, unsafe_allow_html=True)

        with cols[1]:
            st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">🎤</div>
                    <div class="quick-action-text">Voice Input</div>
                </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">🔊</div>
                    <div class="quick-action-text">Voice Output</div>
                </div>
            """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown("""
                <div class="quick-action-card">
                    <div class="quick-action-icon">📋</div>
                    <div class="quick-action-text">Copy & Export</div>
                </div>
            """, unsafe_allow_html=True)

    else:
        # Chat History Display
        for i, msg in enumerate(st.session_state.history):
            # User message
            with st.chat_message("user", avatar="👤"):
                st.markdown(f'<div class="user-message">{msg["user"]}</div>', unsafe_allow_html=True)
                if st.session_state.show_timestamps:
                    st.caption(f"Sent at: {datetime.datetime.now().strftime('%H:%M')}")

            # Assistant message
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f'<div class="assistant-message">{msg["assistant"]}</div>', unsafe_allow_html=True)
                if st.session_state.show_timestamps:
                    st.caption(f"Replied at: {datetime.datetime.now().strftime('%H:%M')}")

                # Message controls
                col1, col2, col3, _ = st.columns([1, 1, 1, 7])
                with col1:
                    if st.button("🔊", key=f"speak_{i}", help="Speak this response"):
                        speak_browser(msg["assistant"])
                        st.success("🔊 Speaking...")

                with col2:
                    if st.button("📋", key=f"copy_{i}", help="Copy this response"):
                        copy_to_clipboard_browser(msg["assistant"])
                        st.success("📋 Copied!")

                with col3:
                    if st.button("⏹️", key=f"stop_{i}", help="Stop speaking"):
                        stop_speaking_browser()
                        st.success("⏹️ Stopped!")

    # Voice Input Section
    st.markdown("---")
    st.markdown("### 🎤 Voice Input")
    listen_browser()

    # Text Input Section
    st.markdown("### 💭 Text Input")
    col_input, col_send = st.columns([9, 1])

    with col_input:
        user_input = st.text_area(
            label="",
            key="message_input",
            placeholder="💭 Type your message here or use voice input above...",
            label_visibility="collapsed",
            value=st.session_state.input_text,
            height=100
        )

    with col_send:
        st.markdown("<br><br>", unsafe_allow_html=True)
        send_clicked = st.button("➡️", help="Send message", use_container_width=True, key="send_btn")

    # Handle send
    if send_clicked and user_input.strip():
        # Add user message
        st.session_state.history.append({"user": user_input, "assistant": "..."})

        # Get AI response
        with st.spinner("🤖 Generating response..."):
            response = handle_command(user_input)
            st.session_state.history[-1]["assistant"] = response

        # Auto-speak if enabled
        if st.session_state.auto_speak:
            speak_browser(response)

        # Clear input and refresh
        st.session_state.input_text = ""
        st.rerun()

    # Quick Actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    quick_cols = st.columns(4)

    with quick_cols[0]:
        if st.button("🕐 Current Time", use_container_width=True, help="Ask for current time"):
            st.session_state.input_text = "What time is it?"
            st.rerun()

    with quick_cols[1]:
        if st.button("📅 Today's Date", use_container_width=True, help="Ask for today's date"):
            st.session_state.input_text = "What's today's date?"
            st.rerun()

    with quick_cols[2]:
        if st.button("💡 Productivity Tip", use_container_width=True, help="Get a useful tip"):
            st.session_state.input_text = "Give me a useful productivity tip"
            st.rerun()

    with quick_cols[3]:
        if st.button("🎲 Random Fact", use_container_width=True, help="Learn something new"):
            st.session_state.input_text = "Tell me an interesting random fact"
            st.rerun()

    # Professional Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; margin-top: 3rem; border-radius: 15px; text-align: center;'>
            <div style='color: white; font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem;'>
                🤖 GenAI Virtual Assistant
            </div>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 1rem;'>
                Professional AI Assistant with Browser-Based Voice Capabilities
            </div>
            <div style='color: rgba(255,255,255,0.7); font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.2);
                        padding-top: 1rem; margin-top: 1rem;'>
                © 2024 Developed by Munesula Vamshi | Powered by OpenRouter API<br>
                Made with ❤️ using Streamlit | All Features Work in Browser
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
