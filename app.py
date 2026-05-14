import streamlit as st
import paho.mqtt.client as mqtt
import json
from PIL import Image
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(page_title="Guardian Vision", page_icon="🛡️", layout="wide")

# ESTILOS (Forzamos visibilidad de texto negro)
st.markdown("""
<style>
.stApp { background-color: white !important; color: black !important; }
.header-box {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 20px; border-radius: 15px; text-align: center; color: white !important;
}
.card {
    background-color: white; padding: 20px; border-radius: 15px;
    border: 2px solid #d1d5db; color: black !important;
}
[data-testid="stSidebar"] { background-color: #f3f4f6 !important; }
.stButton > button {
    background-color: #2563eb !important; color: white !important;
    font-weight: bold; border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h1>🛡️ GUARDIAN VISION</h1><p>Voz + Cámara + MQTT</p></div>', unsafe_allow_html=True)

# =========================================================
# MQTT - VERSIÓN COMPATIBLE UNIVERSAL
# =========================================================
@st.cache_resource
def setup_mqtt():
    # Eliminamos el parámetro que causa el AttributeError para máxima compatibilidad
    client = mqtt.Client() 
    try:
        client.connect("broker.mqttdashboard.com", 1883, 60)
    except:
        pass
    return client

mqtt_client = setup_mqtt()

if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# INTERFAZ
# =========================================================
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎙️ Control por Voz")
    
    # BOTÓN BOKEH (IGUAL AL DE TU EJEMPLO)
    stt_button = Button(label="🎙️ ESCUCHAR", width=250, height=70)
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

    result = streamlit_bokeh_events(stt_button, events="GET_TEXT", key="listen", override_height=90)

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT", "").lower()
        st.markdown(f"<p style='color:black;'><b>Escuchado:</b> {comando}</p>", unsafe_allow_html=True)

        if any(x in comando for x in ["enciende", "activar"]):
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
        elif any(x in comando for x in ["apaga", "desactivar"]):
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    # BOTONES MANUALES
    if st.button("🟢 ENCENDER"):
        st.session_state.alarma_activa = True
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
    if st.button("🔴 APAGAR"):
        st.session_state.alarma_activa = False
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    # ESTADO
    color = "#16a34a" if st.session_state.alarma_activa else "#dc2626"
    texto = "ACTIVADA" if st.session_state.alarma_activa else "DESACTIVADA"
    st.markdown(f"<h2 style='color:{color}; text-align:center;'>{texto}</h2>", unsafe_allow_html=True)

with col2:
    st.markdown("### 📸 Vigilancia")
    foto = st.camera_input("Captura")
    if foto:
        st.image(Image.open(foto), use_container_width=True)
        if st.session_state.alarma_activa:
            st.error("🚨 ALERTA: Intruso detectado")
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "intruso"}))
            
