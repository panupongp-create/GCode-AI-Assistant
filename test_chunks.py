import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from load_data import load_and_split
docs = load_and_split('manual_GCodeV4 (1).pdf')
print(f'Total chunks: {len(docs)}')
for i, d in enumerate(docs[:5]):
    pg = d.metadata.get("page", "?")
    print(f"\n--- Chunk {i} (page {pg}) ---")
    print(d.page_content[:300])
