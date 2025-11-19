from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

def get_model():
    try:
        llm = ChatOllama(
            base_url="http://192.168.1.8:11434",
            model="gpt-oss:20b",    # or gemma3:12b
            temperature=0.7,
            max_tokens=512,
            timeout=None,
            max_retries=2,
            top_k=90,
            top_p=0.5
        )
        return llm
    except Exception as e:
        raise

def get_embedding():
    return OllamaEmbeddings(
        base_url="http://192.168.1.8:11435",
        model="nomic-embed-text"
    )

ollama_llm = get_model()
ollama_embeddings = get_embedding()
