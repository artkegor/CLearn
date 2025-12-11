from langchain_chroma import Chroma
from agents.tutor.embeddings import embeddings
from agents.tutor.config import *


def get_retrievers():
    return {
        "syntax": Chroma(persist_directory=SYNTAX_PATH, embedding_function=embeddings).as_retriever(
            search_kwargs={"k": 20}),
        "control_flow": Chroma(persist_directory=CONTROL_FLOW_PATH, embedding_function=embeddings).as_retriever(
            search_kwargs={"k": 20}),
        "data_structures": Chroma(persist_directory=DATA_STRUCTURES_PATH, embedding_function=embeddings).as_retriever(
            search_kwargs={"k": 20}),
        "functions": Chroma(persist_directory=FUNCTIONS_PATH, embedding_function=embeddings).as_retriever(
            search_kwargs={"k": 20}),
        "memory_files": Chroma(persist_directory=MEMORY_FILES_PATH, embedding_function=embeddings).as_retriever(
            search_kwargs={"k": 20}),
    }
