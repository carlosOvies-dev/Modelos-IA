# -*- coding: utf-8 -*-
import os
import shutil
from mcp.server.fastmcp import FastMCP

# Arranco el servidor MCP y le pongo nombre
mcp = FastMCP("ServidorArchivos")

# Estas son las rutas de las carpetas del proyecto, las guardo en variables para que sea mas comodo usarlas luego
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
CARPETA_BASE = os.path.join(CARPETA_PROYECTO, "base")
CARPETA_RECEPCION = os.path.join(CARPETA_PROYECTO, "recepcion")
CARPETA_CLASIFICADOS = os.path.join(CARPETA_PROYECTO, "clasificados")

# Si las carpetas no existen al bajar el proyecto esto las crea solas para que no de fallo al guardar archivos
os.makedirs(CARPETA_BASE, exist_ok=True)
os.makedirs(CARPETA_RECEPCION, exist_ok=True)
os.makedirs(CARPETA_CLASIFICADOS, exist_ok=True)

# Aqui empiezan las herramientas del servidor MCP.
# El texto que va entre tres comillas debajo de cada def es muy importante porque es lo que lee el modelo para saber que hace cada herramienta.
# La de leer_archivo la uso tanto para que el clasificador saque el texto antes de clasificarlo como por si le pedimos al consultor que nos diga que pone un archivo.
# Al final, como no tenia claro si para ver los clasificados habia que mirar una carpeta en concreto o todas a la vez, hice dos herramientas: una para consultar una sola categoria y otra para listar todas.
@mcp.tool()
def copiar_a_recepcion(nombre_archivo: str) -> str:
    """Copia uno o varios archivos existentes (separados por comas) desde la carpeta base a la carpeta recepcion."""
    # Separo por comas o por la palabra ' y ' por si pido copiar varios archivos a la vez
    nombres = [n.strip() for n in nombre_archivo.replace(" y ", ",").split(",") if n.strip()]
    resultados = []

    for nombre in nombres:
        if not nombre.endswith(".txt"):
            nombre = nombre + ".txt"

        origen = os.path.join(CARPETA_BASE, nombre)
        destino = os.path.join(CARPETA_RECEPCION, nombre)

        if not os.path.exists(origen):
            resultados.append(f"Error: El archivo '{nombre}' no existe en la carpeta base.")
        else:
            shutil.copy2(origen, destino)
            resultados.append(f"El archivo '{nombre}' se ha copiado correctamente a recepción.")

    return "\n".join(resultados)


@mcp.tool()
def guardar_texto_en_recepcion(nombre_archivo: str, texto: str) -> str:
    """Crea un archivo nuevo en la carpeta recepcion con el nombre y el texto indicados."""
    if not nombre_archivo.endswith(".txt"):
        nombre_archivo = nombre_archivo + ".txt"

    ruta_destino = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    with open(ruta_destino, "w", encoding="utf-8") as f:
        f.write(texto)

    return f"El archivo '{nombre_archivo}' se ha creado correctamente en recepción."


@mcp.tool()
def ver_bandeja_recepcion() -> str:
    """Lista los nombres de los archivos pendientes en la carpeta recepcion."""
    archivos = []
    for elemento in os.listdir(CARPETA_RECEPCION):
        ruta_completa = os.path.join(CARPETA_RECEPCION, elemento)
        if os.path.isfile(ruta_completa):
            archivos.append(elemento)

    if len(archivos) == 0:
        return "No hay archivos pendientes en recepción."

    return "\n".join(archivos)


@mcp.tool()
def leer_archivo(nombre_archivo: str) -> str:
    """Lee y devuelve el texto que hay escrito dentro de un archivo de recepcion."""
    if not nombre_archivo.endswith(".txt"):
        nombre_archivo = nombre_archivo + ".txt"

    ruta = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    if not os.path.exists(ruta):
        return f"Error: El archivo '{nombre_archivo}' no está en recepción."

    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read().strip()

    return f"El contenido del archivo '{nombre_archivo}' es: {contenido}"


@mcp.tool()
def mover_a_tema(nombre_archivo: str, tema: str) -> str:
    """Mueve un archivo desde recepcion a la carpeta de su tema dentro de clasificados."""
    if not nombre_archivo.endswith(".txt"):
        nombre_archivo = nombre_archivo + ".txt"

    origen = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    if not os.path.exists(origen):
        return f"Error: No se encontró '{nombre_archivo}' en recepción."

    # Limpio el nombre del tema por si el modelo le pone un punto final y creo su carpeta si no existe
    tema_limpio = tema.strip(" .,;:").capitalize()
    carpeta_tema = os.path.join(CARPETA_CLASIFICADOS, tema_limpio)
    os.makedirs(carpeta_tema, exist_ok=True)

    destino = os.path.join(carpeta_tema, nombre_archivo)
    shutil.move(origen, destino)
    return f"Dentro de la categoría {tema_limpio} se ha guardado: {nombre_archivo}."


@mcp.tool()
def consultar_categoria(categoria: str) -> str:
    """Lista los nombres de los archivos guardados en una categoría concreta (ej. Deportes, Economia, Salud)."""
    nombre_limpio = categoria.strip(" .,;:").capitalize()
    ruta_categoria = os.path.join(CARPETA_CLASIFICADOS, nombre_limpio)

    if not os.path.exists(ruta_categoria):
        return f"La categoría {nombre_limpio} aún no existe."

    archivos = []
    for elemento in os.listdir(ruta_categoria):
        ruta_completa = os.path.join(ruta_categoria, elemento)
        if os.path.isfile(ruta_completa):
            archivos.append(elemento)

    lista_texto = ", ".join(archivos)
    return f"En la categoría {nombre_limpio} están guardados estos archivos: {lista_texto}."


@mcp.tool()
def ver_todas_las_categorias() -> str:
    """Muestra todas las categorías creadas y los archivos que hay dentro de cada una."""
    carpetas = []
    for elemento in os.listdir(CARPETA_CLASIFICADOS):
        ruta_completa = os.path.join(CARPETA_CLASIFICADOS, elemento)
        if os.path.isdir(ruta_completa):
            carpetas.append(elemento)

    if len(carpetas) == 0:
        return "Aún no hay ninguna categoría creada ni archivos clasificados."

    carpetas.sort()
    resumen = []

    for c in carpetas:
        ruta_c = os.path.join(CARPETA_CLASIFICADOS, c)
        archivos_c = []
        for f in os.listdir(ruta_c):
            if os.path.isfile(os.path.join(ruta_c, f)):
                archivos_c.append(f)

        lista_archivos = ", ".join(archivos_c)
        resumen.append(f"- Dentro de la categoría {c} tenemos: {lista_archivos}.")

    return "\n".join(resumen)


if __name__ == "__main__":
    mcp.run(transport="stdio")