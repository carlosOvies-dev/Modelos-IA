# -*- coding: utf-8 -*-
import os
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ServidorArchivos")

CARPETA_BASE = "base"
CARPETA_RECEPCION = "recepcion"
CARPETA_CLASIFICADOS = "clasificados"

os.makedirs(CARPETA_BASE, exist_ok=True)
os.makedirs(CARPETA_RECEPCION, exist_ok=True)
os.makedirs(CARPETA_CLASIFICADOS, exist_ok=True)


@mcp.tool()
def copiar_a_recepcion(nombre_archivo: str) -> str:
    """Copia un archivo desde la carpeta base a la carpeta recepcion."""
    origen = os.path.join(CARPETA_BASE, nombre_archivo)
    destino = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    
    if not os.path.exists(origen):
        return f"Error: El archivo '{nombre_archivo}' no existe en la carpeta base."
    
    shutil.copy2(origen, destino)
    return f"Archivo '{nombre_archivo}' copiado correctamente a recepcion."

@mcp.tool()
def guardar_texto_en_recepcion(nombre_archivo: str, contenido: str) -> str:
    """Crea un archivo de texto plano en la carpeta recepcion con el contenido indicado."""
    if not nombre_archivo.endswith(".txt"):
        nombre_archivo = nombre_archivo + ".txt"
        
    ruta = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
        
    return f"Texto guardado en recepcion como '{nombre_archivo}'."

@mcp.tool()
def listar_recepcion() -> str:
    """Lista todos los archivos disponibles en la carpeta recepcion."""
    archivos = os.listdir(CARPETA_RECEPCION)
    if not archivos:
        return "No hay archivos en recepcion."
    return "\n".join(archivos)

@mcp.tool()
def leer_archivo(nombre_archivo: str) -> str:
    """Lee el contenido de un archivo situado en la carpeta recepcion."""
    ruta = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    
    if not os.path.exists(ruta):
        return f"Error: El archivo '{nombre_archivo}' no existe en recepcion."
        
    with open(ruta, "r", encoding="utf-8") as archivo:
        return archivo.read()

@mcp.tool()
def mover_a_tema(nombre_archivo: str, tema: str) -> str:
    """Crea la carpeta del tema si no existe y mueve el archivo desde recepcion a ese tema."""
    origen = os.path.join(CARPETA_RECEPCION, nombre_archivo)
    carpeta_tema = os.path.join(CARPETA_CLASIFICADOS, tema)
    destino = os.path.join(carpeta_tema, nombre_archivo)
    
    if not os.path.exists(origen):
        return f"Error: No se encontró '{nombre_archivo}' en recepcion."
        
    os.makedirs(carpeta_tema, exist_ok=True)
    shutil.move(origen, destino)
    return f"Archivo '{nombre_archivo}' movido a la carpeta '{tema}'."

@mcp.tool()
def listar_archivos_por_tema(tema: str) -> str:
    """Lista los archivos guardados dentro de la carpeta de un tema específico."""
    carpeta_tema = os.path.join(CARPETA_CLASIFICADOS, tema)
    
    if not os.path.exists(carpeta_tema):
        return f"No existe la carpeta del tema '{tema}' aún."
        
    archivos = os.listdir(carpeta_tema)
    if not archivos:
        return f"No hay archivos en el tema '{tema}'."
    return "\n".join(archivos)


if __name__ == "__main__":
    mcp.run()