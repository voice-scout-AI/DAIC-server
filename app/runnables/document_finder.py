from typing import Dict, Any

from langchain_core.runnables import Runnable

from app.core.decorators import measure_time
from app.core.state import app_state


class DocumentFinder(Runnable):
    def __init__(self):
        self.score_threshold = 1.0

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        query = f"migrating from {input['fromname']} to {input['toname']} key considerations challenges best practices"
        relevant_docs = app_state.vector_store.similarity_search_with_score(query, k=3)

        filtered_docs = [(doc, score) for doc, score in relevant_docs if score <= self.score_threshold]

        reference_docs = "\n\n".join([doc.page_content for doc, score in filtered_docs])

        return {
            **input,
            "reference_docs": reference_docs
        }
