import streamlit as st
from google import genai
from google.genai import types
import openai
from PIL import Image

# Page Configuration
st.set_page_config(
    page_title="Heavy Equipment AI Assistant", 
    page_icon="🔧", 
    layout="centered"
)

# Custom Styling for Workshop Readability
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔧 Heavy Equipment AI Assistant")
st.markdown("Your multi-AI diagnostic, repair, and spec partner for heavy earth-moving machinery.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings & API Keys")
    
    ai_provider = st.selectbox(
        "Choose AI Engine",
        ["Google Gemini", "OpenAI GPT"]
    )
    
    if ai_provider == "Google Gemini":
        api_key = st.text_input("Enter Gemini API Key", type="password")
        model_name = "gemini-2.5-flash"
    else:
        api_key = st.text_input("Enter OpenAI API Key", type="password")
        model_name = "gpt-4o"

    st.markdown("---")
    st.markdown("### 🛠️ Quick Diagnostics")
    
    if st.button("🚨 Decode Error Code"):
        st.session_state.preset_prompt = "Help me decode and troubleshoot this heavy equipment error code. Provide potential causes and fix steps:"
    if st.button("🌊 Hydraulic Flow Issue"):
        st.session_state.preset_prompt = "What are the step-by-step checks for a slow or weak hydraulic circuit on an excavator/loader?"
    if st.button("🔩 Torque Specs Request"):
        st.session_state.preset_prompt = "What safety precautions and general procedures should I follow when checking critical torque specs on heavy machinery components?"

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle preset prompt injection
initial_input = ""
if "preset_prompt" in st.session_state and st.session_state.preset_prompt:
    initial_input = st.session_state.preset_prompt
    st.session_state.preset_prompt = ""

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], caption="Uploaded Machine Photo", width=300)
        st.markdown(message["content"])

# Optional File Uploader for Machinery Photos/Nameplates
uploaded_file = st.file_uploader("📸 Upload Machine Plate, Error Screen, or Broken Part Photo (Optional)", type=["jpg", "jpeg", "png"])

# Chat Input Box
user_prompt = st.chat_input("Describe the machine issue or paste text here...")

# Combine preset if triggered
prompt_to_process = user_prompt if user_prompt else initial_input

if prompt_to_process:
    if not api_key:
        st.error("⚠️ Please enter your API key in the sidebar to proceed.")
    else:
        pil_image = None
        if uploaded_file is not None:
            pil_image = Image.open(uploaded_file)

        user_message_payload = {"role": "user", "content": prompt_to_process, "image": pil_image}
        st.session_state.messages.append(user_message_payload)
        
        with st.chat_message("user"):
            if pil_image:
                st.image(pil_image, caption="Uploaded Machine Photo", width=300)
            st.markdown(prompt_to_process)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing heavy machinery data..."):
                try:
                    system_instruction = (
                        "You are an elite heavy equipment mechanic and diagnostic expert specializing in "
                        "earth-moving machinery, excavators, loaders, bulldozers, and diesel engines. "
                        "Provide clear, structured troubleshooting steps, explicit safety warnings (PPE, pressure release), "
                        "and accurate part/spec recommendations."
                    )
                    
                    reply = ""
                    
                    if ai_provider == "Google Gemini":
                        client = genai.Client(api_key=api_key)
                        
                        contents = [prompt_to_process]
                        if pil_image:
                            contents.append(pil_image)
                            
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction
                            )
                        )
                        reply = response.text

                    elif ai_provider == "OpenAI":
                        client = openai.OpenAI(api_key=api_key)
                        
                        openai_messages = [{"role": "system", "content": system_instruction}]
                        for m in st.session_state.messages:
                            if m["role"] == "user":
                                openai_messages.append({"role": "user", "content": m["content"]})
                            elif m["role"] == "assistant":
                                openai_messages.append({"role": "assistant", "content": m["content"]})
                                
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=openai_messages
                        )
                        reply = response.choices[0].message.content

                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply, "image": None})

                except Exception as e:
                    st.error(f"❌ Error communicating with AI: {e}")
                      
