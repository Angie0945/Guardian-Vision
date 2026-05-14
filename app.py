import streamlit as st
import paho.mqtt.client as mqtt
import json
from PIL import Image
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Guardian Vision",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS (Angie Style - Contraste Mejorado)
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: white !important;
}

/* Forzar que todo el texto base sea negro */
html, body, [class*="css"], .stMarkdown {
    color: black !important;
}

section[data-testid="stSidebar"] {
    background-color: #f3f4f6 !important;
}

section[data-testid="stSidebar"] * {
    color: black !important;
}

.header-box {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
}

.card {
    background-color: white;
    padding: 25px;
    border-radius: 18px;
    border: 2px solid #d1d5db;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Botones manuales */
.stButton > button {
    width: 100%;
    background-color: #2563eb !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 12px !important;
    margin-top: 8px !important;
}

/* Contenedor del botón de voz Bokeh */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="header-box">
    <h1 style="color:white !important; margin:0;">🛡️ GUARDIAN VISION</h1>
    <h3 style="color:white !important; margin:5px;">Sistema Inteligente de Seguridad | Voz + Cámara + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# MQTT CONFIG (Versión compatible Paho 2.0)
# =========================================================
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "voice_ctrl"

@st.cache_resource
def setup_mqtt():
    # Se usa CallbackAPIVersion.VERSION1 para evitar errores de compatibilidad
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "ANGIE_GUARD_PRO")
    try:
        client.connect(BROKER, PORT, 60)
    except:
        pass
    return client

mqtt_client = setup_mqtt()

def enviar_mqtt(mensaje):
    try:
        payload = json.dumps({"Act1": mensaje})
        mqtt_client.publish(TOPIC, payload)
    except:
        pass

# =========================================================
# SESSION STATE
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

if "ultimo_comando" not in st.session_state:
    st.session_state.ultimo_comando = "Esperando voz..."

# =========================================================
# LAYOUT PRINCIPAL
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# PANEL IZQUIERDO: CONTROL
# =========================================================
with col1:
    # Definición de colores según estado
    if st.session_state.alarma_activa:
        panel_bg = "#dcfce7"
        panel_border = "#16a34a"
        panel_text = "#166534"
        estado_texto = "🟢 ALARMA ACTIVADA"
    else:
        panel_bg = "#fee2e2"
        panel_border = "#dc2626"
        panel_text = "#991b1b"
        estado_texto = "🔴 ALARMA DESACTIVADA"

    st.markdown(f"""
    <div style="background-color:{panel_bg}; padding:20px; border-radius:18px; border:3px solid {panel_border}; margin-bottom:20px; text-align:center;">
        <h2 style="color:black; margin:0;">🎙️ Control Inteligente</h2>
    </div>
    """, unsafe_allow_html=True)

    # BOTÓN DE VOZ (BOKEH)
    stt_button = Button(label="🎙️ ESCUCHAR", width=260, height=70, button_type="primary")
    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("El navegador no soporta reconocimiento de voz");
        } else {
            var recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.onresult = function(e) {
                var value = e.results[0][0].transcript;
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            };
            recognition.start();
        }
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=90,
        debounce_time=0
    )

    # PROCESAMIENTO DE VOZ (Corrección de Texto y JSON)
    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT", "").strip().lower()
        st.session_state.ultimo_comando = comando

        # Mensaje de lo que se escuchó con texto NEGRO
        st.markdown(f"""
            <div style="background-color:#f3f4f6; padding:10px; border-radius:10px; border:1px solid #d1d5db; color:black; font-weight:bold; margin-bottom:10px;">
                🎤 Se escuchó: {comando}
            </div>
        """, unsafe_allow_html=True)

        if any(x in comando for x in ["enciende", "activar", "encender"]):
            st.session_state.alarma_activa = True
            enviar_mqtt("activado")
        elif any(x in comando for x in ["apaga", "desactiva", "desactivar", "apagar"]):
            st.session_state.alarma_activa = False
            enviar_mqtt("desactivado")

    # ÚLTIMO COMANDO
    st.markdown("<h4 style='color:black; margin-bottom:0;'>🗣️ Último comando:</h4>", unsafe_allow_html=True)
    st.info(st.session_state.ultimo_comando)

    # BOTONES MANUALES
    if st.button("🟢 ENCENDER ALARMA"):
        st.session_state.alarma_activa = True
        st.session_state.ultimo_comando = "Encendido manual"
        enviar_mqtt("activado")

    if st.button("🔴 APAGAR ALARMA"):
        st.session_state.alarma_activa = False
        st.session_state.ultimo_comando = "Apagado manual"
        enviar_mqtt("desactivado")

    # INDICADOR DE ESTADO FINAL
    st.markdown(f"""
    <div style="background-color:{panel_bg}; padding:20px; border-radius:15px; border:3px solid {panel_border}; text-align:center; margin-top:15px;">
        <h3 style="color:black; margin:0;">📡 Estado</h3>
        <h2 style="color:{panel_text}; margin:0;">{estado_texto}</h2>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# PANEL DERECHO: VIGILANCIA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:black; margin-top:0;'>📸 Cámara de Vigilancia</h2>", unsafe_allow_html=True)

    foto = st.camera_input("Captura de seguridad")

    if foto:
        imagen = Image.open(foto)
        st.image(imagen, caption="Monitoreo en tiempo real", use_container_width=True)

        if st.session_state.alarma_activa:
            st.markdown("""
                <div style="background-color:#fee2e2; border:2px solid #ef4444; padding:15px; border-radius:10px; text-align:center;">
                    <h3 style="color:#991b1b; margin:0;">🚨 ALERTA: Intrusión Detectada</h3>
                </div>
            """, unsafe_allow_html=True)
            enviar_mqtt("intruso")
        else:
            st.markdown("""
                <div style="background-color:#dcfce7; border:2px solid #22c55e; padding:15px; border-radius:10px; text-align:center;">
                    <h3 style="color:#166534; margin:0;">✅ Monitoreo Seguro</h3>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown("<p style='color:black; text-align:center; font-weight:bold;'>Guardian Vision © Angie Vargas - Isabella Saldarriaga - Salome Rivero</p>", unsafe_allow_html=True)
