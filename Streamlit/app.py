import streamlit as st
from detector import analizar_afirmacion

st.set_page_config(page_title="Detector de Fake News — TFM", page_icon="📰", layout="centered")

st.title("Detector de Fake News — TFM")
st.markdown("Introduce una noticia o afirmación y obtén un **veredicto** con el sistema de **agentes**.")

texto = st.text_area("📝 Escribe la noticia o afirmación:", height=320, placeholder="Pega aquí el texto a verificar...")

col1, _ = st.columns([1, 3])
with col1:
    verificar = st.button("🔍 Verificar", type="primary")

if verificar:
    if not texto.strip():
        st.warning("Por favor, escribe una noticia o afirmación.")
    else:
        try:
            with st.spinner("Analizando con el sistema de agentes..."):
                resultado_md = analizar_afirmacion(texto.strip())
            st.success("¡Análisis completado!")
            st.markdown("### 🧾 Resultado")
            st.markdown(resultado_md)
        except Exception as e:
            st.error(f"Ocurrió un error durante el análisis: {e}")


