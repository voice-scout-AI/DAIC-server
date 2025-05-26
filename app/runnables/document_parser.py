from typing import List

from langchain_core.runnables import Runnable
from langchain_upstage import UpstageDocumentParseLoader


class DocumentParser(Runnable):
    def __init__(self):
        return

    def load_document(self, file_paths: List[str]) -> str:
        loader = UpstageDocumentParseLoader(
            file_paths,
            ocr="auto",
            output_format="text",
            coordinates=False
        )
        pages = loader.load()

        combined_text = "\n".join([page.page_content for page in pages])

        return combined_text

    def invoke(self, file_paths: List[str], config=None) -> str:
        return self.load_document(file_paths)
