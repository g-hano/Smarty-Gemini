import fitz
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import json
def extract_text(docs):
    text = ""
    for pdf_path in docs:
        # Open the PDF file
        with fitz.open(pdf_path) as document:
            # Iterate through each page of the document
            for page_num in range(len(document)):
                page = document.load_page(page_num)  # Load the current page
                page_text = page.get_text()  # Extract text from the current page
                text += page_text + "\n"  # Append the extracted text to the cumulative text variable, with a newline for separation
    return text

def split_chunks(text):
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
      )
    chunks = splitter.split_text(text)
    return chunks

def knowledge_base(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="retrieval_query")
    knowledge = FAISS.from_texts(texts=chunks, embedding=embeddings)
    return knowledge


def ask_pdf(pdf_path: str, question: str) -> str:
    def read_pdf(pdf_path: str) -> str:
        full_text = ""
        with fitz.open(pdf_path) as document:        
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                page_text = page.get_text()
                full_text += page_text + "\n"
        return full_text
    
    text = read_pdf(pdf_path)
    chunks = split_chunks(text)
    knowledge = knowledge_base(chunks)
    similarity_search = knowledge.similarity_search(question)

    return similarity_search

from langchain_core.tools import BaseTool
class ASKPDF(BaseTool):
    name = "ask_pdf"
    description = """Extracts text from PDF files and answers questions.
                    Inputs: dictionary of strings that contains pdf path and user question.
                    Outputs: the answer of the question"""
    verbose=True

    def _run(self, inputs: dict[str, str]) -> str:
        inputs = json.loads(inputs)
        try:
            result = ask_pdf(inputs.get("pdf_path"), inputs.get("question"))
        except Exception as e:
            result = e # we return the exception in order to warn the Agent
        return result