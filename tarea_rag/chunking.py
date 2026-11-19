from pathlib import Path
import docx
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# ruta a la carpeta docs usando la ubicacion de este archivo para que funcione desde cualquier sitio
carpeta_docs_defecto = Path(__file__).parent / "docs"
extensiones_validas = {".txt", ".md", ".pdf", ".docx"}


def crear_metadatos(ruta_archivo: Path, **datos_extra) -> dict:
    # guardamos la ruta y el nombre del archivo para saber de donde sale cada trozo
    return {"source": str(ruta_archivo), "doc_key": ruta_archivo.name, **datos_extra}


def leer_texto_o_markdown(ruta_archivo: Path) -> list[Document]:
    # intentamos leer en utf-8 y si falla probamos con el formato tipico de windows
    try:
        contenido = ruta_archivo.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        contenido = ruta_archivo.read_text(encoding="cp1252", errors="replace")

    # si el archivo esta vacio no devolvemos nada
    if not contenido.strip():
        return []
    return [Document(page_content=contenido, metadata=crear_metadatos(ruta_archivo))]


def leer_pdf(ruta_archivo: Path) -> list[Document]:
    # leemos el pdf pagina por pagina para guardar en que pagina esta cada texto
    lector = PdfReader(str(ruta_archivo))
    if lector.is_encrypted:
        lector.decrypt("")

    documentos = []
    for numero_pagina, pagina in enumerate(lector.pages):
        texto_pagina = pagina.extract_text() or ""
        if texto_pagina.strip():
            documentos.append(
                Document(
                    page_content=texto_pagina,
                    metadata=crear_metadatos(ruta_archivo, page=numero_pagina + 1),
                )
            )
    return documentos


def leer_docx(ruta_archivo: Path) -> list[Document]:
    # sacamos primero los parrafos normales del word
    archivo_word = docx.Document(str(ruta_archivo))
    partes = [parrafo.text for parrafo in archivo_word.paragraphs if parrafo.text.strip()]

    # tambien recorremos las tablas del word para no perder los datos que haya ahi
    for tabla in archivo_word.tables:
        for fila in tabla.rows:
            celdas = [celda.text.strip() for celda in fila.cells if celda.text.strip()]
            if celdas:
                partes.append(" | ".join(celdas))

    contenido = "\n".join(partes).strip()
    if not contenido:
        return []
    return [Document(page_content=contenido, metadata=crear_metadatos(ruta_archivo))]


# diccionario para elegir que funcion usar segun la extension del archivo
lectores = {
    ".txt": leer_texto_o_markdown,
    ".md": leer_texto_o_markdown,
    ".pdf": leer_pdf,
    ".docx": leer_docx,
}


def cargar_archivo(ruta_archivo: Path) -> list[Document]:
    funcion_lectora = lectores.get(ruta_archivo.suffix.lower())
    if funcion_lectora is None:
        return []
    try:
        return funcion_lectora(ruta_archivo)
    except Exception as error:
        print(f"Aviso: no se pudo leer {ruta_archivo.name} ({error})")
        return []


def trocear_documentos(
    carpeta_docs: Path = carpeta_docs_defecto,
    tamano_chunk: int = 350,
    solapamiento: int = 60,
) -> list[Document]:
    # comprobamos que el solapamiento no sea mas grande que el propio trozo
    if solapamiento >= tamano_chunk:
        raise ValueError("El solapamiento tiene que ser menor que el tamano del chunk")

    ruta_carpeta = Path(carpeta_docs).resolve()

    # buscamos todos los archivos validos ignorando temporales de word o archivos ocultos
    archivos = sorted(
        archivo
        for archivo in ruta_carpeta.rglob("*")
        if archivo.is_file()
        and archivo.suffix.lower() in extensiones_validas
        and not archivo.name.startswith(("~$", "."))
    )

    if not archivos:
        print(f"No hay documentos validos en {ruta_carpeta}")
        return []

    documentos_completos = []
    for archivo in archivos:
        documentos_completos.extend(cargar_archivo(archivo))

    if not documentos_completos:
        print("No se pudo sacar texto de los documentos")
        return []

    # cortamos el texto intentando respetar parrafos, saltos de linea y frases
    cortador = RecursiveCharacterTextSplitter(
        chunk_size=tamano_chunk,
        chunk_overlap=solapamiento,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks = cortador.split_documents(documentos_completos)

    # le ponemos un identificador unico a cada chunk para poder citarlo luego
    for indice, chunk in enumerate(chunks):
        etiqueta_pagina = f":p{chunk.metadata['page']}" if "page" in chunk.metadata else ""
        nombre_sin_ext = Path(chunk.metadata["doc_key"]).stem
        chunk.metadata["chunk_id"] = f"{nombre_sin_ext}{etiqueta_pagina}:c{indice}"

    print(f"Leidos {len(archivos)} archivos -> {len(documentos_completos)} documentos/paginas -> {len(chunks)} chunks")
    return chunks


# esto solo se ejecuta si lanzamos este archivo directamente para hacer pruebas
if __name__ == "__main__":
    chunks_prueba = trocear_documentos()
    for chunk in chunks_prueba:
        print("-" * 60)
        print(f"ID: {chunk.metadata['chunk_id']} | Caracteres: {len(chunk.page_content)}")
        print(chunk.page_content)
