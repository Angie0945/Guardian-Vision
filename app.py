import streamlit as st
import paho.mqtt.client as paho
import json
from PIL import Image
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Guardian Vision",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILO
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: white;
    color: black;
}
html, body, [class*="css"] {
    color: black !important;
}
section[data-testid="stSidebar"] {
    background-color: #f1f5f9 !important;
}
.header {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    color: white;
}
.card {
    background: #ffffff;
    padding: 20px;
    border-radius: 15px;
    border: 2px solid #d1d5db;
    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
}
.stButton>button {
    background-color: #2563eb;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="header">
    <h1>🛡️ GUARDIAN VISION</h1>
    <h3>Seguridad Inteligente | Voz + MQTT + Cámara</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📘 Instrucciones")
    st.write("### 🎙️ Comandos:")
    st.write("- enciende la alarma")
    st.write("- apaga la alarma")
    st.write("### 📸 Cámara:")
    st.write("Toma fotos para vigilancia.")
    st.write("### 🚨 Sistema:")
    st.write("Solo alerta cuando está activado.")

# =========================================================
# MQTT
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def setup_mqtt():
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "ANGIE_GUARD")
    client.connect(broker, port)
    return client

mqtt_client = setup_mqtt()

# =========================================================
# SESSION
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# LAYOUT
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# CONTROL VOZ
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("🎙️ Control por Voz")

    stt_button = Button(label="🎙️ ESCUCHAR", width=220, height=70)

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';

        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript;
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        };

        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen"
    )

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").lower()

        st.success(f"🗣️ {comando}")

        if "enciende" in comando:
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

        elif "apaga" in comando:
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    st.write("### 🔘 Control Manual")

    if st.button("🟢 ENCENDER"):
        st.session_state.alarma_activa = True

    if st.button("🔴 APAGAR"):
        st.session_state.alarma_activa = False

    if st.session_state.alarma_activa:
        st.error("🔴 ALARMA ACTIVADA")
    else:
        st.success("🟢 ALARMA APAGADA")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# CÁMARA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📸 Cámara de Vigilancia")

    img_file = st.camera_input("Toma una captura")

    if img_file:
        img = Image.open(img_file)

        st.image(img, use_container_width=True)

        if st.session_state.alarma_activa:
            st.error("🚨 Revisa la captura por posible intruso")
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "intruso"}))
        else:
            st.success("Área monitoreada sin alarma activa.")

    st.markdown("</div>", unsafe_allow_html=True)
