from langchain_nvidia import ChatNVIDIA
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader,PyPDFLoader
from langchain_core.prompts import ChatMessagePromptTemplate,ChatPromptTemplate
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.chains import LLMChain
import streamlit as st
import os

load_dotenv()
os.environ["NVIDIA_API_KEY"] = os.getenv("NVIDIA_API_KEY")
os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")


def file_process(file_uploader):

    all_docs = []
    if file_uploader is not None:

        for file_uploader in file_uploader:
            with open(f"./temp/{file_uploader.name}",'wb') as f:
                f.write(file_uploader.getbuffer())
            loader = PyPDFLoader(f"./temp/{file_uploader.name}")
            docs = loader.load()
            all_docs.extend(docs)
    
    return all_docs

def vectore_function(docs):
    if "vectore" not in st.session_state:
        
        st.session_state.embedding = NVIDIAEmbeddings()
        #st.session_state.loader = PyPDFDirectoryLoader("./pdf")
        #st.session_state.pdf = st.session_state.loader.load()
        st.session_state.text_spliter = RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=70)
        st.session_state.spliter = st.session_state.text_spliter.split_documents(docs[:30])
        st.session_state.vectore = FAISS.from_documents(st.session_state.spliter,st.session_state.embedding)


template_prompt = ChatPromptTemplate.from_template(

    """
        your work to give the answer to the user question from using 
        context. please try to use attractive emoji or give the most accurcate and  
        similar answer from the context if answer is seems 
        similar so write the Sorry we don't have a answer yet!.

        <context>
        {context}
        <context>

        Question:{input}

    """
)


llm = ChatNVIDIA(model="nvidia/llama-3.1-nemotron-70b-instruct")

st.set_page_config(page_title="Langchain: Question/Answering Chat bot",page_icon="🦜")
st.title('🦜LangChain')
st.title("Title: Question/Answering Chat bot")
st.subheader("How to use:")

st.write("Step1: Upload your document. Please ensure that the document is in PDF format.")

st.write("""Step2: Click on the 'Embed Document' button and wait. During this step,the entire document will be embedded and stored in the database.
           Wait until the database setup is complete.""")  
    
st.write("""Step3: Once the database is ready, a text box will appear where you can
            ask question based on the stored document.""")

st.write("Step4: Enter your question in the text box and press Enter to receive answers.")

st.write("⚠️Step 1: Upload the document then go to another steps")
file_uploader = st.file_uploader("Upload the only pdf",type='pdf',accept_multiple_files=True)

if file_uploader is not None:
    #st.write(f"file name:{file_uploader.name}")
    os.makedirs(f"./temp",exist_ok=True)
    upload_docs = file_process(file_uploader)
    st.write(f"length of the uploaded document: {len(upload_docs)}")

st.write("⚠️Step2: Click on the 'Embed document' button and wait for the database is successfully ready")
if st.button("Embed the document"):
    vectore_function(upload_docs)
    st.write("Sucessfully database is ready")

st.write("⚠️After completing all the requirements then you ask your question")
user_input = st.text_area("Ask you any question from the documentation")

if st.button("👉Generate the answer"):
    if user_input:
        chain_stuff = create_stuff_documents_chain(llm=llm,prompt=template_prompt)
        retriever = st.session_state.vectore.as_retriever()
        chain_retriever = create_retrieval_chain(retriever,chain_stuff)
        response = chain_retriever.invoke({"input":user_input})
        st.write(response['answer'])

        if "context" in response:
            with st.expander("Similar document:"):
                for i,doc in enumerate(response['context']):
                    st.write(doc.page_content)
                    st.write("---------------------")   

        else:
            st.write("context is not provide in the response")