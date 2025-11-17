import streamlit as st
import nbformat
import os
import time
from docx import Document
import google.generativeai as genai

# --- PAGE CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="SurakshaMesh X | Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (THE PRO LOOK) ---
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0e1117;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: #1e2329;
        border: 1px solid #2b313a;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #ffffff;
    }
    .metric-label {
        font-size: 14px;
        color: #8b949e;
        margin-bottom: 5px;
    }
    
    /* Critical Alert Animation */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
        70% { box-shadow: 0 0 0 20px rgba(255, 75, 75, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
    }
    .critical-alert {
        background-color: #3d0c0c;
        border: 2px solid #ff4b4b;
        color: #ff4b4b;
        padding: 20px;
        border-radius: 10px;
        animation: pulse 2s infinite;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    /* Chat Bubbles */
    .chat-user {
        background-color: #2b313a;
        padding: 15px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        color: #e6edf3;
    }
    .chat-bot {
        background-color: #1e2329;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
        color: #e6edf3;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
DEFAULT_MODEL = "models/gemini-1.5-flash"

# --- 1. THE PERSONAS ---
COMMANDER_SYSTEM = """
You are the 'SurakshaMesh Chief Safety Officer'.
Your goal: Analyze incoming worker telemetry and issue immediate safety commands.

INPUT DATA:
You will receive a JSON string with: Worker ID, Risk Score, Sensor Data (Gas, Heart Rate), and Duration.

YOUR OUTPUT RULES:
1. ANALYZE:
   - Gas > 300 OR Fire = True -> CRITICAL EMERGENCY (Act Immediately).
   - Score > 80 AND Duration > 5s -> CRITICAL (Persistent Danger).
   - Score > 80 AND Duration < 5s -> MONITOR (Likely Sensor Spike).
   - Score < 50 -> NORMAL.
2. INSTRUCT (Hinglish):
   - Give clear, shouting-style instructions like a Supervisor.
   - Example: "Ramesh! Gas leak confirm hua hai. Turant Zone B se bahar niklo!"
3. EXPLAIN:
   - Briefly cite the sensor reading that triggered the alarm.

FORMAT:
## 🚨 DECISION: [CRITICAL / MONITOR / NORMAL]
**Action Plan:**
* [Step 1]
* [Step 2]

**🔊 Audio Script (Hinglish):**
"[Your Hinglish Warning Here]"
"""

ARCHITECT_SYSTEM = """
You are the 'SurakshaMesh X Architect'.
You have memorized the project Blueprint, Code, and Idea Description.
Answer technical questions based ONLY on the context provided.
"""

# --- 2. SIMPLE FILE LOADER ---
@st.cache_data
def load_full_context():
    context_text = ""
    docx_files = ["Suraksha Mesh X Blueprint V3.docx", "Surakshamesh V3 Idea Description.docx"]
    for file in docx_files:
        if os.path.exists(file):
            try:
                doc = Document(file)
                text = "\n".join([para.text for para in doc.paragraphs])
                context_text += f"\n\n=== DOCUMENT: {file} ===\n{text}"
            except: pass
    ipynb_file = "update_masterfile__do_include_the_codes_and_final_.ipynb"
    if os.path.exists(ipynb_file):
        try:
            with open(ipynb_file, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
                for cell in nb.cells:
                    if cell.cell_type == 'code':
                        context_text += f"\n\n=== CODE SNIPPET ===\n{cell.source}\n"
        except: pass
    return context_text

# --- 3. AI FUNCTIONS ---
def get_ai_response(system_prompt, user_input, context="", api_key=None, model_name=""):
    if not api_key:
        time.sleep(1.5)
        # Enhanced Simulation Logic
        if "incoming worker telemetry" in system_prompt.lower() or "json" in user_input.lower():
            return """## 🚨 DECISION: CRITICAL
**Action Plan:**
* **IMMEDIATE EVACUATION:** Activate Zone B Klaxon.
* **ISOLATION:** Shut down Valve V-402.
* **DEPLOY:** Send Drone Squad Alpha.

**🔊 Audio Script (Hinglish):**
"Ramesh! Suno! Gas leak confirm hua hai! Turant upar waale raste se Zone B khaali karo!"
"""
        else:
            return "**[DEMO MODE]** Based on Blueprint V3, the SX1276 connects via SPI (MISO:19, MOSI:23, SCK:18, NSS:5). Connect DIO0 to GPIO 2."

    try:
        genai.configure(api_key=api_key)
        full_prompt = f"SYSTEM INSTRUCTION: {system_prompt}\n\nCONTEXT: {context}\n\nUSER INPUT: {user_input}"
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- 4. THE UI LAYOUT ---

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9564/9564063.png", width=80)
    st.title("SurakshaMesh X")
    st.caption("v3.0 | Architect Edition")
    st.divider()
    
    api_key = st.text_input("🔐 Gemini API Key", type="password")
    
    selected_model = DEFAULT_MODEL
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if models:
                selected_model = st.selectbox("🧠 AI Model", models, index=0)
        except: pass
        
    st.divider()
    st.info("Status: System Online 🟢")

# Tabs
tab1, tab2 = st.tabs(["🚨 COMMANDER DASHBOARD", "🧠 ARCHITECT CHAT"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("### 🏭 Real-Time Safety Operations")
    
    # Input Section
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("#### 📡 Live Telemetry Feed")
        default_json = """{
  "worker_id": "W-102",
  "risk_score": 92,
  "sensors": { "gas_ppm": 450, "heart_rate": 120 },
  "duration_seconds": 12,
  "zone": "Furnace_B"
}"""
        telemetry = st.text_area("Raw Sensor Stream", default_json, height=250)
        analyze_btn = st.button("⚡ ANALYZE RISK DATA", use_container_width=True, type="primary")
        
    with col2:
        st.markdown("#### 📊 Signal Visualization")
        # Metric Cards Layout
        m1, m2, m3 = st.columns(3)
        
        # Simple parsing for visual effect (demo purposes)
        try:
            import json
            data = json.loads(telemetry)
            risk = data.get("risk_score", 0)
            gas = data.get("sensors", {}).get("gas_ppm", 0)
            hr = data.get("sensors", {}).get("heart_rate", 0)
        except:
            risk, gas, hr = 0, 0, 0
            
        m1.markdown(f'<div class="metric-card"><div class="metric-label">RISK SCORE</div><div class="metric-value" style="color: {"#ff4b4b" if risk > 80 else "#00cc00"}">{risk}%</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-label">GAS (PPM)</div><div class="metric-value">{gas}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-label">HEART RATE</div><div class="metric-value">{hr} BPM</div></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Output Area
        result_container = st.container()
        if analyze_btn:
            with st.spinner("🧠 AI Brain Analyzing Pattern..."):
                response = get_ai_response(COMMANDER_SYSTEM, telemetry, api_key=api_key, model_name=selected_model)
                
                if "CRITICAL" in response:
                    st.markdown('<div class="critical-alert">🚨 CRITICAL HAZARD DETECTED 🚨</div>', unsafe_allow_html=True)
                
                st.markdown("#### 🛡️ Commander Action Plan")
                st.markdown(response)

# --- TAB 2: ARCHITECT CHAT ---
with tab2:
    st.markdown("### 🧠 Project Knowledge Base")
    
    # Load Context
    if "file_context" not in st.session_state:
        with st.spinner("indexing project files..."):
            st.session_state.file_context = load_full_context()
    
    # Chat Interface
    chat_container = st.container()
    
    # Input fixed at bottom
    user_q = st.chat_input("Ask about Blueprints, Code, or Hardware...")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display Chat
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">👤 <b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bot">🤖 <b>Architect:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        st.rerun()

    # Handle Response after rerun (to show user msg first)
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        latest_q = st.session_state.chat_history[-1]["content"]
        with st.spinner("Architect is thinking..."):
            ans = get_ai_response(ARCHITECT_SYSTEM, latest_q, st.session_state.file_context, api_key, selected_model)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()