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

# Busco la ruta donde esta servicio_mcp.py y preparo los parametros para que se arranque solo
ruta_servidor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servicio_mcp.py")

server_params = StdioServerParameters(
    command=sys.executable,
    args=[ruta_servidor],
    env=None
)


# Uso esta funcion para leer por teclado sin que se quede bloqueado el programa al ser asincrono
async def ainput(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def main():
    # Cargo el modelo (segun lo que haya en el .env cogera gemini u ollama)
    llm = obtener_llm()

    # Creo el id de la sesion para que el grafo guarde la memoria de la conversacion
    config = {"configurable": {"thread_id": "sesion_clase"}}

    # Arranco y conecto el servidor MCP en segundo plano
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Saco las herramientas que tenemos en servicio_mcp.py
            mcp_tools = await load_mcp_tools(session)

            # Monto el grafo pasandole el modelo y las herramientas
            app = crear_grafo(llm, mcp_tools)

            # Bucle para hablar con el agente por consola
            while True:
                pregunta = await ainput("\nUsuario>>> ")

                # Si escribo salir se cierra el programa
                if pregunta.strip().lower() in ["salir", "exit", "quit"]:
                    break

                # Si doy al enter sin escribir nada, vuelve a preguntar
                if not pregunta.strip():
                    continue

                # Si escribo reiniciar, cambio el id de sesion para empezar con la memoria limpia
                if pregunta.strip().lower() == "reiniciar":
                    config = {"configurable": {"thread_id": f"sesion_{os.urandom(4).hex()}"}}
                    print("¡Memoria limpia y nueva sesión iniciada!")
                    continue

                # Meto la pregunta del usuario y llamo al grafo pasandole la configuracion de memoria
                inputs = {"messages": [HumanMessage(content=pregunta)]}
                resultado = await app.ainvoke(inputs, config=config)
                
                # Cojo el ultimo mensaje que devuelve el grafo y lo muestro por pantalla
                respuesta_final = resultado["messages"][-1].content
                print(f"Respuesta:\n{respuesta_final}")


if __name__ == "__main__":
    asyncio.run(main())