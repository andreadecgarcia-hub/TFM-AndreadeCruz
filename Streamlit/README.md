Aplicación web (carpeta Streamlit/)
Ejecutar en local
cd streamlit
pip install -r requirements.txt
Configura la clave de OpenAI mediante Secrets locales de Streamlit 
Crea el archivo .streamlit/secrets.toml dentro de streamlit/:
OPENAI_API_KEY = "sk-XXXXXXXX"
OPENAI_MODEL   = "gpt-4o-mini"
Lanza la app:
streamlit run app.py

Despliegue (Streamlit Cloud / Hugging Face Spaces)
Define el secreto OPENAI_API_KEY en Settings → Secrets (Streamlit) o Settings → Repository secrets (HF Spaces).
