import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
GOOGLE_GEMINI_KEY = os.getenv('GOOGLE_API_KEY')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for sessions

class QuestionGenerator:
    def __init__(self, google_api_key, model_name="gemini-pro"):
        self.model_name = model_name
        self.google_api_key = google_api_key

    def get_conversational_chain_ques(self):
        prompt_template_ques = """
        Based on the provided context, provide me five questions that are related to the context and test the understanding of the context by a user in a list format.
        Context:\n {context}?\n
        questions=['question 1','question 2','question 3'.....,'question 5']
        """
        model = ChatGoogleGenerativeAI(model=self.model_name, temperature=0.3, google_api_key=self.google_api_key)
        prompt = PromptTemplate(template=prompt_template_ques, input_variables=["context"])
        chain_ques = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        return chain_ques

    def generate_questions(self, context):
        chain_ques = self.get_conversational_chain_ques()
        response = chain_ques({"input_documents": [Document(page_content=context)]}, return_only_outputs=True)
        questions = response["output_text"]
        q_list = questions.split('\n')
        q_list = [q.split('. ', 1)[1] for q in q_list if q]
        return q_list

class QAProcessor:
    def __init__(self, google_api_key, faiss_index_path="faiss_index"):
        self.google_api_key = google_api_key
        self.faiss_index_path = faiss_index_path
        self.vector_store = self.load_vector_store()

    def load_vector_store(self):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=self.google_api_key)
        if os.path.exists(self.faiss_index_path):
            return FAISS.load_local(self.faiss_index_path, embeddings, allow_dangerous_deserialization=True)
        else:
            return None

    def get_vector_store(self, text_chunks):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=self.google_api_key)
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local(self.faiss_index_path)
        return vector_store

    def user_input(self, question, answer):
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized. Please create or load the FAISS index.")
        
        docs = self.vector_store.similarity_search(question)
        prompt_template = """
        Based on the provided context, verify if the provided answer to the question is correct. If the answer is correct, reply with 'Yes, the answer is correct.' 
        Otherwise, reply with 'No, the answer is incorrect' and provide the correct answer with an explanation.

        Context:\n {context}?\n
        Question: \n{question}\n
        Provided Answer: \n{answer}\n

        Response:
        """
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, google_api_key=self.google_api_key)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question", "answer"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

        response = chain({"input_documents": docs, "question": question, "answer": answer}, return_only_outputs=True)
        return response["output_text"]

def get_pdf_text(pdf_file):
    if pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    else:
        raise FileNotFoundError("No PDF file provided.")

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def generate_ques(text, num_chars=10000):
    max_start = len(text) - num_chars
    if max_start < 0:
        max_start = 0
    x = random.randint(0, max_start)
    y = x + num_chars
    return text[x:y]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if pdf_file:
            raw_text = get_pdf_text(pdf_file)
            context = generate_ques(raw_text)
            question_generator = QuestionGenerator(google_api_key=GOOGLE_GEMINI_KEY)
            questions = question_generator.generate_questions(context)

            return render_template('examination.html', questions=questions)

    return render_template('chat.html')

@app.route('/check_answer', methods=['POST'])
def check_answer():
    question = request.form['question']
    user_answer = request.form['answer']

    qa_processor = QAProcessor(google_api_key=GOOGLE_GEMINI_KEY)
    response = qa_processor.user_input(question, user_answer)

    return render_template('examination.html', questions=[question], responses=[response])

if __name__ == '__main__':
    app.run(debug=True)
