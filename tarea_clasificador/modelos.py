# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

# Aqui cargo las variables de entorno, en ellas se pueden cambiar tanto el modelo de gemini como el de ollama y la Api de gemini.
# Uso variables de entorno porque me parece mas facil y limpio a la hora de configurar las cosas sin tener que estar buscando una variable por el codigo
load_dotenv()


def obtener_llm():
    # Miro si hay metida una API key de gemini
    clave = os.getenv("API_KEY_IA", "").strip()

    # Si la clave no esta vacia usamos gemini cogiendo el modelo del .env
    if clave != "":
        nombre_modelo = os.getenv("MODELO_GEMINI")
        return ChatGoogleGenerativeAI(
            model=nombre_modelo,
            google_api_key=clave
        )
    # Si esta vacia usamos ollama por defecto con su modelo y su url del .env
    else:
        print("[Aviso] No hay API_KEY_IA en .env -> Usando Ollama por defecto.")
        nombre_modelo = os.getenv("MODELO_OLLAMA")
        url_ollama = os.getenv("URL_OLLAMA")
        return ChatOllama(
            model=nombre_modelo,
            temperature=0,
            base_url=url_ollama
        )