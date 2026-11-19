# Sistema RAG sobre animales marinos

Proyecto en Python que implementa un sistema RAG (Generacion Aumentada por Recuperacion) sobre una coleccion propia de documentos de animales marinos (artemia, tiburon cebra, morena y corales) en formatos `txt`, `md`, `docx` y `pdf`.

## Estructura del proyecto
- `docs/`: carpeta con los documentos de texto.
- `chunking.py`: lee los archivos y los divide en trozos (chunks) con solapamiento.
- `indexar.py`: convierte los chunks en vectores y los guarda en ChromaDB.
- `chat_rag.py`: abre un chat por terminal que busca la informacion relevante en ChromaDB y usa un LLM (Ollama en local o Gemini) para responder solo con lo que hay en los documentos.
- `requirements.txt`: lista de librerias necesarias.
- `.env.example`: plantilla para configurar la clave de la API.

## Instalacion

1. Clona el repositorio y entra en la carpeta del proyecto:
```bash
git clone [https://github.com/carlosOvies-dev/Modelos-IA.git](https://github.com/carlosOvies-dev/Modelos-IA.git)
cd Modelos-IA/tarea_rag
```

2. Crea y activa un entorno virtual (recomendado Python 3.12):
```bash
python3 -m venv .venv
source .venv/bin/activate
```
(Si usas `uv`: `uv venv --python 3.12 && source .venv/bin/activate`)

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```
(O con `uv`: `uv pip install -r requirements.txt`)

4. Configura las variables de entorno (solo si vas a usar Gemini):
```bash
cp .env.example .env
```
Abre `.env` y pega tu `GOOGLE_API_KEY`. Si vas a usar Ollama en local, asegurate de tenerlo arrancado.

## Uso

1. Indexa los documentos en ChromaDB:
```bash
python indexar.py
```

2. Inicia el chat para hacer preguntas:
```bash
python chat_rag.py
```
