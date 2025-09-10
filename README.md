# TFM-AndreadeCruz
El presente trabajo tiene como propósito diseñar e implementar un sistema multiagente para la verificación de noticias, con el objetivo de analizar su viabilidad como apoyo frente a la desinformación.  

Este repositorio contiene dos piezas independientes:
colab/ – Notebook de experimentación y evaluación.
streamlit/ – Aplicación web de demostración (UI) en Streamlit.

Requisitos: 
Una API key de OpenAI con acceso al modelo indicado (por defecto gpt-4o-mini).

1) Notebook (carpeta colab/)
Abre colab/Código_Google_Colab_TFM.ipynb en Google Colab.
Ejecuta la primera celda para instalar dependencias:
%pip -q install -r Requirements.txt
La celda de configuración te pedirá la API key (o puedes definirla como variable de entorno OPENAI_API_KEY).
El notebook lee el dataset desde:
EXCEL_PATH = "dataset_pruebas.xlsx"
y guarda resultados en:
OUTPUT_CSV = "resultados_con_evidencias.csv"

2)App web (carpeta streamlit/)
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

