from typing import Dict, Any

from langchain_core.runnables import Runnable

from app.core.state import app_state


class DocumentFinder(Runnable):
    def __init__(self):
        self.score_threshold = 1.0

    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        query = f"{input['fromname']}에서 {input['toname']}로 conversion시 주의해야할 것"
        relevant_docs = app_state.vector_store.similarity_search_with_score(query, k=3)

        filtered_docs = [(doc, score) for doc, score in relevant_docs if score <= self.score_threshold]

        for doc, score in filtered_docs:
            print(f"{score:4f} {doc}")

        reference_docs = "\n\n".join([doc.page_content for doc, score in filtered_docs])

        return {
            **input,
            "reference_docs": reference_docs
        }
