from app.runnables.code_generator import CodeGenerator
from app.runnables.document_finder import DocumentFinder


class CodeTransformerChain:
    def __init__(self):
        self.chain = (
                DocumentFinder()
                | CodeGenerator()
        )

    def invoke(self, input):
        result = self.chain.invoke(input)

        return result
