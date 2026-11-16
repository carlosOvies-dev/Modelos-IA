# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

# Cargamos las variables del archivo .env
load_dotenv()

def obtener_llm(tipo=None, nombre_modelo=None):
    # Leemos la clave de Google del archivo .env
    clave = os.getenv("API_KEY_IA", "").strip()

    # Si no nos pasan el tipo o si la clave de Google esta vacia, usamos Ollama
    if tipo is None:
        if clave != "" and clave != "tu_clave_de_google_aqui":
            tipo = "gemini"
        else:
            print("[Aviso] No hay API_KEY_IA válida en .env -> Usando Ollama por defecto.")
            tipo = "ollama"

    if tipo == "gemini":
        if nombre_modelo is None:
            nombre_modelo = os.getenv("MODELO_GEMINI", "gemini-2.5-flash")
        return ChatGoogleGenerativeAI(
            model=nombre_modelo,
            google_api_key=clave,
            temperature=0
        )
    elif tipo == "ollama":
        if nombre_modelo is None:
            nombre_modelo = os.getenv("MODELO_OLLAMA", "llama3.1:8b-instruct-q4_K_M")
        url_ollama = os.getenv("URL_OLLAMA", "http://localhost:11434")
        return ChatOllama(
            model=nombre_modelo,
            temperature=0,
            base_url=url_ollama
        )
    else:
        raise ValueError("El tipo debe ser 'gemini' o 'ollama'")