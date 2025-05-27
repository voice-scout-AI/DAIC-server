import json
import os
from typing import Optional

import faiss
from langchain.schema import Document
from langchain_community.docstore import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings


class VectorStore():
    def __init__(self):
        self.vector_store = None
        self.initialize_vector_store()

    def initialize_vector_store(self):
        embeddings = UpstageEmbeddings(model="embedding-query")

        index = faiss.IndexFlatL2(len(embeddings.embed_query("React 18 이상으로 업그레이드할 때는 컴포넌트 클래스말고 함수로 선언해야함.")))

        self.vector_store = FAISS(
            embedding_function=embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )

        documents = self.load_documents_from_json()
        self.vector_store.add_documents(documents)

    def load_documents_from_json(self) -> list[Document]:
        json_path = os.path.join(os.path.dirname(__file__), "document.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        for doc_data in data.get("documents", []):
            document = Document(
                page_content=doc_data["page_content"],
                metadata=doc_data["metadata"]
            )
            documents.append(document)

        return documents

    def search_similar_documents(self, query: str, k: int = 5, filter_dict: Optional[dict] = None):
        if filter_dict:
            results = self.vector_store.similarity_search_with_score(query, k=k, filter=filter_dict)
        else:
            results = self.vector_store.similarity_search_with_score(query, k=k)

        return results
