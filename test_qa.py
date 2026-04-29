import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from load_data import load_and_split
from vector_db import create_vector_db
from chatbot import create_chatbot

print('1. Loading PDF...')
docs = load_and_split('manual_GCodeV4 (1).pdf')
print(f'   Loaded {len(docs)} chunks')

print('2. Creating vector DB (multilingual)...')
db = create_vector_db(docs)

print('3. Creating chatbot...')
qa = create_chatbot(db)

print('4. Testing retriever...')
results = db.similarity_search("G Code คืออะไร", k=3)
for i, r in enumerate(results):
    print(f"   Result {i}: {r.page_content[:150]}...")

print('\n5. Asking: G Code คืออะไร')
answer = qa.invoke('G Code คืออะไร')
print(f'Answer: {answer}')
