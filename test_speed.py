import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from load_data import load_and_split
from vector_db import create_vector_db
from chatbot import create_chatbot, ask_question

print('Loading...')
docs = load_and_split('V9 คู่มือ Gcode  Version_9 28042569.pdf')
db = create_vector_db(docs)
chatbot = create_chatbot(db)

print('Asking...')
start = time.time()
result = ask_question(chatbot, 'G Code คืออะไร')
elapsed = time.time() - start

print(f'Time: {elapsed:.1f}s')
print(f'Answer: {result["answer"]}')
