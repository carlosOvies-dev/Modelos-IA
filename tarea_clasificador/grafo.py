# -*- coding: utf-8 -*-
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, AIMessage

# 1. Lista prefijada de temas iniciales
TEMAS_VALIDOS = ["Deportes", "Economia", "Tecnologia", "Salud"]


# 2. Estado del grafo (guarda la conversación y el siguiente nodo)
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str


# 3. Función auxiliar para limpiar el texto que devuelve el modelo
def extraer_texto(respuesta) -> str:
    contenido = respuesta.content
    if isinstance(contenido, list):
        if len(contenido) > 0 and isinstance(contenido[0], dict) and "text" in contenido[0]:
            return contenido[0]["text"].strip()
        return str(contenido[0]).strip()
    return str(contenido).strip()


# 4. Función que construye el grafo
def crear_grafo(llm, mcp_tools, modo_clasificador="A"):
    """
    Construye el grafo de agentes.
    modo_clasificador: "A" (Agente ReAct autónomo) o "B" (Flujo dirigido en Python).
    """

    mapa_tools = {t.name: t for t in mcp_tools}

    tools_recepcion = [
        mapa_tools["copiar_a_recepcion"],
        mapa_tools["guardar_texto_en_recepcion"],
        mapa_tools["listar_recepcion"]
    ]
    tools_clasificador = [
        mapa_tools["listar_recepcion"],
        mapa_tools["leer_archivo"],
        mapa_tools["mover_a_tema"]
    ]
    tools_consultor = [
        mapa_tools["listar_archivos_por_tema"]
    ]

    # --- NODO ENRUTADOR ---
    async def nodo_enrutador(state: AgentState):
        mensaje_usuario = state["messages"][-1].content
        prompt = (
            "Eres un enrutador. Clasifica la petición del usuario en una de estas 3 opciones:\n"
            "- Si pide copiar/subir un archivo, guardar un texto nuevo o ver qué hay en recepción, responde: recepcion\n"
            "- Si pide clasificar, organizar o mover los archivos de recepción por temas, responde: clasificador\n"
            "- Si pide listar o consultar los archivos de un tema concreto, responde: consultor\n\n"
            "Responde ÚNICAMENTE con una palabra en minúsculas (recepcion, clasificador o consultor).\n"
            f"Mensaje: {mensaje_usuario}"
        )
        respuesta = await llm.ainvoke(prompt)
        destino = extraer_texto(respuesta).lower()

        if "clasificador" in destino:
            destino = "clasificador"
        elif "consultor" in destino:
            destino = "consultor"
        else:
            destino = "recepcion"

        print(f" [Enrutador] -> Enviando a: {destino.upper()}")
        return {"next_agent": destino}

    # --- NODO RECEPCIÓN ---
    async def nodo_recepcion(state: AgentState):
        agente = create_react_agent(llm, tools=tools_recepcion)
        prompt = SystemMessage(
            content="Eres el encargado de recepción. Usa tus herramientas para copiar archivos "
                    "desde base a recepcion, o guardar textos nuevos como archivos en recepcion."
        )
        res = await agente.ainvoke({"messages": [prompt] + state["messages"]})
        return {"messages": [res["messages"][-1]]}

    # =========================================================================
    # VERSIÓN A DEL CLASIFICADOR: Agente ReAct Autónomo
    # Diferencia: La IA decide sola qué herramienta llamar en cada paso (3-4 llamadas al LLM).
    # =========================================================================
    async def nodo_clasificador_A(state: AgentState):
        agente = create_react_agent(llm, tools=tools_clasificador)
        temas_str = ", ".join(TEMAS_VALIDOS)
        prompt = SystemMessage(
            content=f"Eres el agente clasificador. Lista de temas prefijados: [{temas_str}]. "
                    "1. Usa 'listar_recepcion' para ver los archivos pendientes. "
                    "2. Usa 'leer_archivo' para leer el contenido de cada uno. "
                    "3. Elige su tema de la lista prefijada (si no encaja en ninguno, crea un tema nuevo de una sola palabra) "
                    "y usa 'mover_a_tema' para moverlo a su carpeta."
        )
        res = await agente.ainvoke({"messages": [prompt] + state["messages"]})
        return {"messages": [res["messages"][-1]]}

    # =========================================================================
    # VERSIÓN B DEL CLASIFICADOR: Flujo Dirigido por Python
    # Diferencia: Python llama a listar/leer/mover en orden fijo.
    # La IA solo interviene 1 vez por archivo para decidir el tema (ahorra tokens).
    # =========================================================================
    async def nodo_clasificador_B(state: AgentState):
        # 1. Python llama a la tool MCP para listar los archivos en recepción
        texto_lista = await mapa_tools["listar_recepcion"].ainvoke({})
        if "No hay archivos" in texto_lista or not texto_lista.strip():
            return {"messages": [AIMessage(content="No hay archivos pendientes en recepción.")]}

        archivos = [linea.strip() for linea in texto_lista.split("\n") if linea.strip()]
        resumen = []

        # 2. Recorremos cada archivo en Python
        for nombre in archivos:
            # Python llama a la tool MCP para leer el contenido
            contenido = await mapa_tools["leer_archivo"].ainvoke({"nombre_archivo": nombre})
            temas_str = ", ".join(TEMAS_VALIDOS)

            # ÚNICA llamada a la IA: elige un tema de la lista o inventa uno nuevo si no encaja
            prompt = (
                f"Clasifica este texto usando uno de estos temas prefijados: [{temas_str}].\n"
                "Si el texto no encaja en ninguno de la lista, responde con un tema nuevo de una sola palabra.\n"
                "Responde ÚNICAMENTE con la palabra del tema (primera letra en mayúscula, sin puntos).\n"
                f"Texto: {contenido}"
            )
            res_ia = await llm.ainvoke(prompt)
            tema_elegido = extraer_texto(res_ia).capitalize()

            # Si la IA ha creado un tema nuevo que no estaba en la lista, lo añadimos
            if tema_elegido not in TEMAS_VALIDOS:
                TEMAS_VALIDOS.append(tema_elegido)

            # 3. Python llama a la tool MCP (crea la carpeta del tema si no existe y mueve el archivo)
            resultado_mover = await mapa_tools["mover_a_tema"].ainvoke({
                "nombre_archivo": nombre,
                "tema": tema_elegido
            })
            resumen.append(resultado_mover)

        mensaje_final = "\n".join(resumen)
        return {"messages": [AIMessage(content=mensaje_final)]}

    # --- NODO CONSULTOR ---
    async def nodo_consultor(state: AgentState):
        agente = create_react_agent(llm, tools=tools_consultor)
        temas_str = ", ".join(TEMAS_VALIDOS)
        prompt = SystemMessage(
            content=f"Eres el agente consultor. Temas conocidos actualmente: [{temas_str}]. "
                    "Usa la herramienta 'listar_archivos_por_tema' para responder al usuario."
        )
        res = await agente.ainvoke({"messages": [prompt] + state["messages"]})
        return {"messages": [res["messages"][-1]]}

    # --- CONSTRUCCIÓN DEL GRAFO ---
    grafo = StateGraph(AgentState)

    grafo.add_node("enrutador", nodo_enrutador)
    grafo.add_node("recepcion", nodo_recepcion)
    grafo.add_node("consultor", nodo_consultor)

    if modo_clasificador == "A":
        grafo.add_node("clasificador", nodo_clasificador_A)
    else:
        grafo.add_node("clasificador", nodo_clasificador_B)

    grafo.add_edge(START, "enrutador")

    def leer_decision(state: AgentState):
        return state["next_agent"]

    grafo.add_conditional_edges(
        "enrutador",
        leer_decision,
        {
            "recepcion": "recepcion",
            "clasificador": "clasificador",
            "consultor": "consultor"
        }
    )

    grafo.add_edge("recepcion", END)
    grafo.add_edge("clasificador", END)
    grafo.add_edge("consultor", END)

    return grafo.compile()