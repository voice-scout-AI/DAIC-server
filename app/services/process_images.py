from typing import List

from app.runnables.candidate_finder import CandidateFinder
from app.runnables.code_analyser import CodeAnalyser
from app.runnables.code_cleaner import CodeCleaner
from app.runnables.document_parser import DocumentParser


class ImageProcessorChain:
    def __init__(self):
        self.chain = (
                DocumentParser()
                | CodeCleaner()
                | CodeAnalyser()
                | CandidateFinder()
        )

    def invoke(self, image_paths: List[str]) -> any:
        result = self.chain.invoke(image_paths)
        return result


if __name__ == "__main__":
    processor = ImageProcessorChain()

    result = processor.invoke(["/Users/eunjongkim/PycharmProjects/DAIC-server/app/statics/test_img_0.png",
                               "/Users/eunjongkim/PycharmProjects/DAIC-server/app/statics/test_img_1.png"])
    print("처리 결과 ->")
    print(result)
