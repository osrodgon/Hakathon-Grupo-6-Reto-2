# backend/tools/build_vectorstore.py
import os, glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "pdfs_madrid")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore_cache")
os.makedirs(OUT_DIR, exist_ok=True)

print(f"📚 Leyendo PDFs de: {os.path.abspath(PDF_DIR)}")
pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
if not pdfs:
    raise SystemExit("No se encontraron PDFs. Verifica la carpeta 'backend/pdfs_madrid'.")

docs = []
for pdf in pdfs:
    print(f"  - {os.path.basename(pdf)}")
    for d in PyPDFLoader(pdf).load():
        docs.append(d)

print(f"🧩 {len(docs)} documentos. Dividiendo en chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
chunks = splitter.split_documents(docs)
print(f"🧩 {len(chunks)} chunks generados.")

print("🔢 Creando embeddings (Sentence-Transformers)...")
emb = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("🧠 Construyendo índice FAISS...")
vs = FAISS.from_documents(chunks, emb)

print(f"💾 Guardando índice en: {os.path.abspath(OUT_DIR)}")
vs.save_local(OUT_DIR)

print("✅ ¡Vectorstore cache creada! (index.faiss + index.pkl)")
