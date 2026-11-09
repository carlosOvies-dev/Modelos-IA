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