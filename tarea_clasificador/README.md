# Agente Clasificador de Archivos con LangGraph y MCP

Este proyecto implementa un sistema multiagente con **LangGraph** conectado a un servidor de herramientas **MCP (Model Context Protocol)** para crear, consultar y clasificar automáticamente archivos de texto (`.txt`) por temáticas. Permite trabajar tanto con **Google Gemini** como en local con **Ollama** configurando únicamente el archivo `.env`.

## Estructura del Proyecto

- `main.py`: Punto de entrada asíncrono. Inicia el servidor MCP en segundo plano, gestiona la sesión de memoria (`thread_id`), el comando `reiniciar` y el bucle de conversación por consola.
- `modelos.py`: Carga las variables de entorno desde `.env`. Si detecta una clave en `API_KEY_IA`, utiliza Gemini; si está vacía, utiliza Ollama por defecto.
- `servicio_mcp.py`: Servidor `FastMCP` que expone 7 herramientas para gestionar los archivos entre las carpetas `base/`, `recepcion/` y `clasificados/`.
- `grafo.py`: Define el grafo de estados con `MemorySaver`, un nodo `enrutador` y 3 nodos especialistas (`recepcion`, `consultor` y `clasificador`).
- `.env.example`: Plantilla con las variables de entorno necesarias para ejecutar el programa.

## Requisitos Previos

1. **Python 3.10 o superior**.
2. **Gestor de paquetes `uv`** (o `pip`).
3. **Ollama** instalado y ejecutándose en local (si se va a usar sin API Key de Gemini), o una **API Key de Google Gemini**.

## Instalación Paso a Paso

1. **Clonar el repositorio y entrar en la carpeta del proyecto:**

       git clone <URL_DEL_REPOSITORIO>
       cd tarea_clasificador

2. **Crear y activar el entorno virtual:**

       uv venv
       source .venv/bin/activate

3. **Instalar las dependencias del proyecto:**

       uv sync

4. **Descargar el modelo local en Ollama (solo si se va a usar Ollama):**

       ollama pull qwen2.5:7b-instruct

## Configuración del archivo .env

1. **Copia el archivo de ejemplo `.env.example` y renómbralo a `.env`:**

       cp .env.example .env

2. **Abre el archivo `.env` y rellénalo según el modo que quieras usar:**

       # Si dejo la clave vacia el programa usa Ollama por defecto, si pongo mi clave usa Gemini
       API_KEY_IA=

       # Nombre del modelo de Gemini a usar cuando hay clave
       MODELO_GEMINI=gemini-3.6-flash

       # Modelo local descargado en Ollama y la direccion donde escucha
       MODELO_OLLAMA=qwen2.5:7b-instruct
       URL_OLLAMA=http://localhost:11434

   - **Para usar Ollama en local:** Deja `API_KEY_IA=` vacío y asegúrate de que `MODELO_OLLAMA` coincida con el modelo que tienes descargado en Ollama.
   - **Para usar Gemini:** Escribe tu clave después del signo igual en `API_KEY_IA=tu_clave_aqui`.

## Ejecución y Uso

No es necesario arrancar `servicio_mcp.py` en otra terminal, ya que `main.py` lo inicia y conecta automáticamente. Ejecuta:

    python main.py

### Comandos especiales en consola

- **`reiniciar`**: Limpia la memoria de la conversación actual iniciando una sesión nueva.
- **`salir`** / **`exit`** / **`quit`**: Cierra la conexión MCP y finaliza el programa.

### Ejemplos de órdenes para probar el agente

- **Recepción (crear o copiar archivos):**
  - `copia el archivo nota1 a recepcion`
  - `crea un archivo llamado partido y que contenga: El partido de baloncesto empieza a las seis`
- **Consultor (listar, leer y memoria):**
  - `que archivos hay pendientes en recepcion`
  - `lee el archivo partido`
  - `¿De qué trataba el archivo que acabas de leer?`
- **Clasificador (uno o todos los archivos):**
  - `clasifica el archivo partido`
  - `clasifica todos los archivos pendientes`
- **Consulta de categorías:**
  - `que archivos hay en la categoria Deportes`
  - `muestrame todas las categorias`