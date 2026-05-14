# ========================= SIDEBAR (REEMPLAZAR TODO EL SIDEBAR ACTUAL) =========================
with st.sidebar:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        min-width: 340px !important;
        max-width: 340px !important;
        background-color: #f4f4f4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📘 GUÍA DE USO")
    st.success("🟢 Panel abierto automáticamente")

    with st.expander("🚀 Instrucciones completas", expanded=True):

        st.markdown("""
### 🎤 CONTROL POR VOZ
**Paso 1:** Presiona el botón **🎙️ ESCUCHAR**  
**Paso 2:** Di uno de estos comandos:

**Activar sistema:**  
🗣️ *“enciende la alarma”*

**Desactivar sistema:**  
🗣️ *“apaga la alarma”*

---

### 🎛️ CONTROL MANUAL
También puedes usar botones:

🔴 **ACTIVAR ALARMA**  
🟢 **DESACTIVAR ALARMA**

---

### 📸 CÁMARA INTELIGENTE
Cuando el sistema esté activo:

✅ Detecta personas automáticamente  
🚨 Envía alerta MQTT  
🗣️ Genera mensajes de seguridad  

---

### 🌟 TECNOLOGÍA
- 🎤 Voz  
- 📷 Visión Artificial  
- 🌐 MQTT  
- 🤖 YOLO
        """)

    st.write("---")
    st.subheader("🛡️ Guardian Vision")
    st.write("Sistema multimodal de seguridad física + digital.")


# ========================= ELIMINAR RECTÁNGULOS VACÍOS DESPUÉS DEL HEADER =========================
# BORRA cualquier línea como:
# st.markdown('<div class="card">', unsafe_allow_html=True)
# que esté VACÍA o antes de contenido real.
# SOLO deja tarjetas cuando tengan contenido.


# ========================= BOTONES MANUALES MEJORADOS =========================
st.write("### 🎛️ Control Manual del Sistema")

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🔴 ACTIVAR ALARMA\nEncender vigilancia inteligente"):
        st.session_state.alarma_activa = True
        mqtt_client.publish(
            "voice_ctrl",
            json.dumps({"Act1": "activado"})
        )
        st.error("🔴 Sistema activado correctamente")

with col_btn2:
    if st.button("🟢 DESACTIVAR ALARMA\nApagar vigilancia"):
        st.session_state.alarma_activa = False
        mqtt_client.publish(
            "voice_ctrl",
            json.dumps({"Act1": "desactivado"})
        )
        st.success("🟢 Sistema desactivado correctamente")


# ========================= MEJORA VISUAL BOTONES =========================
st.markdown("""
<style>

/* Botones con alto contraste */
.stButton>button {
    background-color: black !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: bold !important;
    border-radius: 14px !important;
    padding: 18px !important;
    border: 2px solid black !important;
    white-space: pre-line !important;
    min-height: 95px !important;
}

/* Hover */
.stButton>button:hover {
    background-color: #333333 !important;
    color: white !important;
    border: 2px solid #111111 !important;
}

/* Eliminar espacios vacíos innecesarios */
.block-container {
    padding-top: 1.5rem !important;
}

/* Texto negro global */
html, body, [class*="css"] {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)
