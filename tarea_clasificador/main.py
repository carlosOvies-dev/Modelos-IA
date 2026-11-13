# -*- coding: utf-8 -*-
import asyncio
import sys
import os
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from modelos import obtener_llm
from grafo import crear_grafo

# Configuramos los parámetros para arrancar servicio_mcp.py automáticamente
ruta_servidor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servicio_mcp.py")

server_params = StdioServerParameters(
    command=sys.executable,
    args=[ruta_servidor],
    env=None
)


# Función para leer por teclado sin bloquear asyncio
async def ainput(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


# Función principal asíncrona
async def main():
    # Seleccionamos el modelo ("gemini" u "ollama")
    llm = obtener_llm("gemini", "gemini-2.5-flash")
    # llm = obtener_llm("ollama", "llama3.1:8b-instruct-q4_K_M")

    # Elegimos qué versión del clasificador usar ("A" = Agente ReAct, "B" = Dirigido Python)
    modo_clasificador = "A"

    # Conectamos con el servidor MCP en segundo plano
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Cargamos todas las herramientas de servicio_mcp.py
            mcp_tools = await load_mcp_tools(session)

            # Construimos el grafo pasándole el modelo, las tools y el modo elegido
            app = crear_grafo(llm, mcp_tools, modo_clasificador=modo_clasificador)

            while True:
                pregunta = await ainput("\nUsuario>>> ")

                if pregunta.strip().lower() in ["salir", "exit", "quit"]:
                    break

                if not pregunta.strip():
                    continue

                inputs = {"messages": [HumanMessage(content=pregunta)]}
                resultado = await app.ainvoke(inputs)
                respuesta_final = resultado["messages"][-1].content

                print(f"Respuesta:\n{respuesta_final}")


if __name__ == "__main__":
    asyncio.run(main())