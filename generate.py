# generate.py
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq LLM
llm = ChatGroq(temperature=0.7, groq_api_key=groq_api_key, model_name="llama-3.1-70b-versatile")

# Define the output parser
json_parser = JsonOutputParser()

# Define the MCQ prompt template with fixed JSON formatting
mcq_prompt_template = PromptTemplate(
    input_variables=["text"],
    template="""Based on the following text, generate 10 multiple-choice questions (MCQs) with 4 options each. 
    Ensure that one option is correct and the others are plausible but incorrect.
    Make sure the questions are not repeated and conform to the given text.
    Format the output as a JSON array with each question object containing a question, choices array, answer, and points.
    
    Text: {text}
    
    Return the output in this exact format:
    [
        {{
            "question": "Question text here",
            "choices": [
                "a) Option A text",
                "b) Option B text",
                "c) Option C text",
                "d) Option D text"
            ],
            "answer": "Correct option in full",
            "points": 20
        }}
    ]"""
)

def setup_qa_chain(text):
    # Create text splitter
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    # Create embeddings and vector store
    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.from_texts(chunks, embeddings)
    
    # Create memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
    )
    
    return qa_chain

def generate_mcqs(text):
    # Combine the prompt template and output parser
    chain = mcq_prompt_template | llm | json_parser
    
    try:
        # Generate MCQs
        result = chain.invoke({"text": text})
        return result
    except OutputParserException as e:
        st.error(f"Error parsing output: {e}")
        return None