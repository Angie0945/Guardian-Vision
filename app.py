# =========================
# REEMPLAZA SOLO EL BLOQUE:
# with col1:
# =========================

with col1:

    # =====================================================
    # COLOR DINÁMICO SEGÚN ESTADO
    # =====================================================
    if st.session_state.alarma_activa:
        panel_bg = "#fee2e2"      # rojo claro
        panel_border = "#dc2626"  # rojo intenso
        panel_text = "#991b1b"    # rojo oscuro
        estado_texto = "🔴 ALARMA ACTIVADA"
    else:
        panel_bg = "#dcfce7"      # verde claro
        panel_border = "#16a34a"  # verde intenso
        panel_text = "#166534"    # verde oscuro
        estado_texto = "🟢 ALARMA DESACTIVADA"

    # =====================================================
    # PANEL PERSONALIZADO
    # =====================================================
    st.markdown(f"""
    <div style="
        background-color:{panel_bg};
        padding:25px;
        border-radius:18px;
        border:3px solid {panel_border};
        box-shadow:0px 4px 15px rgba(0,0,0,0.08);
        margin-bottom:20px;
    ">
        <h2 style="color:black; text-align:center;">🎙️ Control Inteligente</h2>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # BOTÓN DE VOZ
    # =====================================================
    stt_button = Button(label="🎙️ ESCUCHAR", width=240, height=70)

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();

        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript;
            document.dispatchEvent(
                new CustomEvent("GET_TEXT", {detail: value})
            );
        };

        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=90,
        debounce_time=0
    )

    # =====================================================
    # PROCESAR COMANDOS
    # =====================================================
    if result and "GET_TEXT" in result:
        comando = result["GET_TEXT"].strip().lower()
        st.session_state.ultimo_comando = comando

        if "enciende" in comando:
            st.session_state.alarma_activa = True
            enviar_mqtt("activado")

        elif "apaga" in comando:
            st.session_state.alarma_activa = False
            enviar_mqtt("desactivado")

    # =====================================================
    # ÚLTIMO COMANDO
    # =====================================================
    st.markdown("<h3 style='color:black;'>🗣️ Último comando:</h3>", unsafe_allow_html=True)
    st.info(st.session_state.ultimo_comando)

    # =====================================================
    # BOTONES MANUALES
    # =====================================================
    if st.button("🟢 ENCENDER ALARMA"):
        st.session_state.alarma_activa = True
        st.session_state.ultimo_comando = "Encendido manual"
        enviar_mqtt("activado")

    if st.button("🔴 APAGAR ALARMA"):
        st.session_state.alarma_activa = False
        st.session_state.ultimo_comando = "Apagado manual"
        enviar_mqtt("desactivado")

    # =====================================================
    # ESTADO DEL SISTEMA
    # =====================================================
    st.markdown(f"""
    <div style="
        background-color:{panel_bg};
        padding:20px;
        border-radius:15px;
        border:3px solid {panel_border};
        text-align:center;
        margin-top:20px;
    ">
        <h3 style="color:black;">📡 Estado del Sistema</h3>
        <h2 style="color:{panel_text};">{estado_texto}</h2>
    </div>
    """, unsafe_allow_html=True)
