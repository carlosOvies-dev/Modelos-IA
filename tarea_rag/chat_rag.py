import os
from pathlib import Path
from typing import TypedDict
import chromadb
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from sentence_transformers import SentenceTransformer

# cargamos las variables del .env que esta en esta carpeta
carpeta_actual = Path(__file__).parent
load_dotenv(carpeta_actual / ".env")


def leer_variable(nombre: str) -> str:
    # si la variable no esta en el .env o esta vacia, paramos el programa y avisamos
    valor = os.getenv(nombre)
    if not valor or not valor.strip():
        raise ValueError(f"Falta configurar la variable {nombre} en el archivo .env")
    return valor.strip()


carpeta_chroma = carpeta_actual / "chroma_rag"
nombre_coleccion = "animales_marinos"
nombre_modelo_embeddings = leer_variable("MODELO_EMBEDDINGS")

# configuracion de busqueda: cuantos trozos traer y que parecido minimo exigir
numero_resultados = 3
umbral_similitud = 0.40


def crear_modelo_chat() -> ChatOpenAI:
    # aqui si permitimos que API_KEY_IA este vacia porque es el interruptor para usar Ollama
    clave_api = (os.getenv("API_KEY_IA") or "").strip()

    if clave_api:
        modelo_gemini = leer_variable("MODELO_GEMINI")
        print(f"Usando modelo en la nube: Gemini ({modelo_gemini})")
        return ChatOpenAI(
            model=modelo_gemini,
            api_key=clave_api,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=0,
        )
    else:
        modelo_ollama = leer_variable("MODELO_OLLAMA")
        url_ollama = leer_variable("URL_OLLAMA")
        print(f"Usando modelo local: Ollama ({modelo_ollama})")
        return ChatOpenAI(
            model=modelo_ollama,
            api_key="ollama",  # ollama no pide clave real pero la libreria obliga a poner texto
            base_url=url_ollama,
            temperature=0,
        )


# cargamos el modelo de embeddings, la base de datos y el chat una sola vez al arrancar
print(f"Cargando embeddings ({nombre_modelo_embeddings}) y abriendo ChromaDB...")
modelo_embeddings = SentenceTransformer(nombre_modelo_embeddings)
cliente_chroma = chromadb.PersistentClient(path=str(carpeta_chroma))
coleccion = cliente_chroma.get_collection(name=nombre_coleccion)
modelo_chat = crear_modelo_chat()


# definimos la mochila de datos que va pasando de un nodo a otro en langgraph
class EstadoRAG(TypedDict):
    pregunta: str
    contexto: str
    fuentes: list[str]
    respuesta: str


def nodo_recuperar(estado: EstadoRAG) -> dict:
    # pasamos la pregunta a numeros y buscamos los trozos mas cercanos en chroma
    vector_pregunta = modelo_embeddings.encode(
        [estado["pregunta"]], normalize_embeddings=True
    ).tolist()

    resultado = coleccion.query(
        query_embeddings=vector_pregunta,
        n_results=numero_resultados,
        include=["documents", "metadatas", "distances"],
    )

    trozos_validos = []
    fuentes_validas = []

    for doc_id, texto, distancia in zip(
        resultado["ids"][0], resultado["documents"][0], resultado["distances"][0]
    ):
        similitud = round(1 - distancia, 2)
        # solo nos quedamos con los trozos que superen el parecido minimo
        if similitud >= umbral_similitud:
            trozos_validos.append(f"[{doc_id}] {texto}")
            fuentes_validas.append(f"{doc_id} (similitud: {similitud})")

    contexto_unido = "\n\n".join(trozos_validos)
    return {"contexto": contexto_unido, "fuentes": fuentes_validas}


def nodo_generar(estado: EstadoRAG) -> dict:
    # si ningun trozo paso el filtro, avisamos directamente sin gastar llamada al modelo
    if not estado["contexto"]:
        return {
            "respuesta": "No tengo informacion relevante en los documentos para responder a esa pregunta."
        }

    # le damos instrucciones claras al modelo para que no se invente nada
    mensaje = f"""Eres un asistente que responde preguntas usando UNICAMENTE la informacion del contexto.
Si la respuesta no aparece claramente en el contexto, di exactamente que no tienes esa informacion en los documentos.
Responde en espanol de forma clara y directa.

Contexto:
{estado['contexto']}

Pregunta: {estado['pregunta']}
"""
    respuesta_modelo = modelo_chat.invoke(mensaje)
    return {"respuesta": respuesta_modelo.content}


# montamos el grafo: inicio -> recuperar -> generar -> fin
constructor = StateGraph(EstadoRAG)
constructor.add_node("recuperar", nodo_recuperar)
constructor.add_node("generar", nodo_generar)
constructor.add_edge(START, "recuperar")
constructor.add_edge("recuperar", "generar")
constructor.add_edge("generar", END)
grafo_rag = constructor.compile()


if __name__ == "__main__":
    print("\nChat RAG listo. Escribe 'salir' para terminar.\n")
    while True:
        pregunta_usuario = input("Tu: ").strip()
        if not pregunta_usuario:
            continue
        if pregunta_usuario.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break

        resultado_final = grafo_rag.invoke({"pregunta": pregunta_usuario})

        print(f"\nAsistente: {resultado_final['respuesta']}")
        if resultado_final["fuentes"]:
            print(f"Fuentes usadas: {', '.join(resultado_final['fuentes'])}")
        print("-" * 60)
