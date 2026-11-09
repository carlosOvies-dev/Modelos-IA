# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

# 1. Cargamos el archivo .env
load_dotenv()

# funcion para saber que modelo vamos a usar
def obtener_llm(tipo, nombre_modelo):
    if tipo == "gemini":
        # Si es gemini leemos la api key
        clave = os.getenv("API_KEY_IA")
        return ChatGoogleGenerativeAI(
            model=nombre_modelo,
            google_api_key=clave,
            temperature=0
        )
    elif tipo == "ollama":
        # Si es ollama esta en nuestro pc de forma local
        return ChatOllama(
            model=nombre_modelo,
            temperature=0
        )
    else:
        raise ValueError("El tipo debe ser 'gemini' o 'ollama'")