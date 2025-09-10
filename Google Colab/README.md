Notebook (carpeta Google Colab/)

Abre colab/Código_Google_Colab_TFM.ipynb en Google Colab.

Ejecuta la primera celda para instalar dependencias:

%pip -q install -r Requirements.txt

La celda de configuración te pedirá la API key (o puedes definirla como variable de entorno OPENAI_API_KEY).

El notebook lee el dataset desde:

EXCEL_PATH = "dataset_pruebas.xlsx"

y guarda resultados en:

OUTPUT_CSV = "resultados_con_evidencias.csv"
