import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chunking import trocear_documentos

# cargamos las variables del archivo .env que esta en esta misma carpeta
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


def limpiar_metadatos(chunk) -> dict:
    # chroma solo acepta textos, numeros o booleanos en los metadatos asi que nos quedamos con lo basico
    datos = {
        "source": chunk.metadata["source"],
        "doc_key": chunk.metadata["doc_key"],
        "start_index": chunk.metadata.get("start_index", 0),
    }
    if "page" in chunk.metadata:
        datos["page"] = chunk.metadata["page"]
    return datos


def indexar_documentos(tamano_chunk: int = 350, solapamiento: int = 60):
    # sacamos los trozos de texto usando nuestro script de chunking
    chunks = trocear_documentos(tamano_chunk=tamano_chunk, solapamiento=solapamiento)
    if not chunks:
        print("No hay chunks para guardar en ChromaDB.")
        return

    textos = [chunk.page_content for chunk in chunks]

    print(f"Cargando modelo de embeddings ({nombre_modelo_embeddings})...")
    modelo_embeddings = SentenceTransformer(nombre_modelo_embeddings)

    # convertimos todos los trozos en vectores de numeros
    vectores = modelo_embeddings.encode(
        textos,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=True,
    )
    print(f"Vectores creados con forma: {vectores.shape}")

    # abrimos chroma en disco para que los datos no se borren al cerrar el programa
    cliente = chromadb.PersistentClient(path=str(carpeta_chroma))

    # si ya habia una coleccion de antes la borramos para empezar limpios y no duplicar
    colecciones_existentes = [c.name for c in cliente.list_collections()]
    if nombre_coleccion in colecciones_existentes:
        cliente.delete_collection(nombre_coleccion)

    coleccion = cliente.create_collection(
        name=nombre_coleccion,
        metadata={"hnsw:space": "cosine"},
    )

    # guardamos los datos por lotes por si algun dia metemos documentos muy largos
    tamano_lote = 1000
    for inicio in range(0, len(chunks), tamano_lote):
        fin = inicio + tamano_lote
        coleccion.add(
            ids=[chunk.metadata["chunk_id"] for chunk in chunks[inicio:fin]],
            embeddings=vectores[inicio:fin].tolist(),
            documents=textos[inicio:fin],
            metadatas=[limpiar_metadatos(chunk) for chunk in chunks[inicio:fin]],
        )

    print(f"Listo: {coleccion.count()} chunks guardados en {carpeta_chroma}")
    return modelo_embeddings, coleccion


if __name__ == "__main__":
    modelo_prueba, coleccion_prueba = indexar_documentos(tamano_chunk=350, solapamiento=60)

    # hacemos una busqueda rapida para ver si encuentra bien cosas sin usar el llm todavia
    pregunta_prueba = "Que temperatura necesita la artemia para eclosionar?"
    vector_pregunta = modelo_prueba.encode([pregunta_prueba], normalize_embeddings=True).tolist()
    resultado = coleccion_prueba.query(
        query_embeddings=vector_pregunta,
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nPrueba de busqueda: {pregunta_prueba}")
    for doc_id, texto, distancia in zip(
        resultado["ids"][0], resultado["documents"][0], resultado["distances"][0]
    ):
        similitud = round(1 - distancia, 2)
        print(f"  Similitud: {similitud} | [{doc_id}] -> {texto[:90].replace(chr(10), ' ')}...")
