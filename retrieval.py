from vectordb import Memory
import os
from sentence_transformers import CrossEncoder, SentenceTransformer
import spacy
import faiss

NLP = spacy.load("it_core_news_sm")

def tokenize_with_overlap(file_name, max_length=128, overlap=2):
    text = ''
    try:
        with open(file_name, 'r',  encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f" '{file_name}' non è stato trovato.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

    text = text.replace('\n', ' ')

    doc = NLP(text)
    sentences = [sent.text for sent in doc.sents]
    
    tokenized_blocks = []
    current_block = []
    length = 0
    
    for sent in sentences:
        sent_length = len(NLP(sent))
        
        if length + sent_length > max_length:
            tokenized_blocks.append(" ".join(current_block))
            current_block = current_block[-overlap:]
            length = sum(len(NLP(sent)) for sent in current_block)
        
        current_block.append(sent)
        length += sent_length
    
    if current_block:
        tokenized_blocks.append(" ".join(current_block))
    
    return tokenized_blocks

def return_cross_encoder(model_name, query, titles):
    documents = []
    chunks = []
    for name in titles:
        doc = {
            'name_original_file': name,
            'sentences': []
        }
        if name.endswith(".txt"):
            text = tokenize_with_overlap('Full_dataset_chatFAQ/'+name)
            doc['sentences'] = text
            for t in text:
                chunks.append(t)
        documents.append(doc)

    cross_encoder = CrossEncoder(model_name)

    ranks = cross_encoder.rank(query, chunks, return_documents=True, show_progress_bar=True, apply_softmax=True)
    ranks = [item for item in ranks if item['score'] > 0]

    origin_files = []
    scores = []
    stop = False

    for item in ranks[:30]:
        if not stop:
            for doc in documents:
                sentences = doc['sentences']
                phase = ' '.join(sentences)
                if item['text'] in phase:
                    if len(origin_files) == 3: 
                        stop = True
                        break
                    if doc["name_original_file"] not in origin_files:
                        origin_files.append(doc["name_original_file"])
                        scores.append(item['score'])
                        documents.remove(doc)
                    break

    return origin_files, scores

def usage_mem (query, top_k):

    memory = Memory(memory_file='vectordb_stored')

    ''' 
    # STORAGE DOCUMENTS IN THE MEMORY
    files = os.listdir('Full_dataset_chatFAQ/')
    files.sort()

    texts = []
    metadata_list = []

    for filename in files:
        doc = {
            'name_original_file': filename,
            'sentences': []
        }
        if filename.endswith(".txt"):
            with open('Full_dataset_chatFAQ/'+filename, 'r') as file:
                texts.append(file.read())
                
                infos = {
                    'title': filename
                }
                metadata_list.append(infos)
    memory.save(texts, metadata_list, memory_file='new_vecdb')
    '''

    results = memory.search(query, top_k, unique=True)

    return results

def usage_faiss(query, top_k):
    files = os.listdir('Full_dataset_chatFAQ/')
    files.sort()

    metadata_list = []

    for filename in files:
        if filename.endswith(".txt"):
            infos = {
                'title': filename
            }
            metadata_list.append(infos)

    model = SentenceTransformer('nickprock/sentence-bert-base-italian-uncased')

    '''
    # CREATION OF THE INDEX SPACE
    embedded = model.encode(texts)
    index = faiss.IndexFlatL2(embedded.shape[1])
    index.add(embedded)
    faiss.write_index(index, 'index_faiss2')
    '''

    index = faiss.read_index('index_faiss')

    query_vector = model.encode([query])
    distances, top_docs = index.search(query_vector, top_k) 
    results = [(metadata_list[_id]) for i, _id in enumerate(top_docs[0])]
    
    return results

def ret_docs(query):
    docs_mem = usage_mem(query, 8)
    docs_faiss = usage_faiss(query, 8)

    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    docs = [t['metadata']['title'] for t in docs_mem]
    unify = [t['title'] for t in docs_faiss]

    for x in unify:
        if x not in docs:
            docs.append(x)

    origin_files, scores = return_cross_encoder(model_name, query, docs)
    return origin_files, scores