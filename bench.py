from pathlib import Path
import re
import sys

from src import Document, EmbeddingStore, HeadingChunker, OpenAIEmbedder, _mock_embed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("data/ecommerce")
QUERIES = [
    ("Thời hạn người mua gửi yêu cầu trả hàng là bao lâu?", {"audience": "buyer"}),
    ("Người bán phải thực hiện bảo hành theo thông tin nào?", {"audience": "seller"}),
    ("TikTok hỗ trợ người mua khi người bán từ chối bảo hành thế nào?", {"audience": "buyer"}),
    ("Người bán cần khai báo thông tin bảo hành nào khi đăng sản phẩm?", {"audience": "seller"}),
    ("Có những hình thức bảo hành nào cho hàng đã qua sử dụng?", {"audience": "seller"}),
]


def load_documents():
    documents = []
    for path in sorted(DATA_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        _, frontmatter, content = raw.split("---", 2)
        metadata = dict(re.findall(r"^(\w+):\s*[\"']?(.+?)[\"']?\s*$", frontmatter, re.M))
        chunks = HeadingChunker(chunk_size=450).chunk(content.strip())
        for index, chunk in enumerate(chunks):
            documents.append(Document(f"{path.stem}#{index}", chunk, {**metadata, "doc_id": path.stem}))
    return documents


def main():
    provider = __import__("os").environ.get("EMBEDDING_PROVIDER", "mock").lower()
    embedder = OpenAIEmbedder() if provider == "openai" else _mock_embed
    print(f"Embedding backend: {getattr(embedder, '_backend_name', 'mock')}")
    store = EmbeddingStore(embedding_fn=embedder)
    documents = load_documents()
    store.add_documents(documents)
    print(f"Loaded {len(documents)} chunks from {len(list(DATA_DIR.glob('*.md')))} documents")
    for number, (query, metadata_filter) in enumerate(QUERIES, 1):
        print(f"\nQ{number}: {query}\nfilter={metadata_filter}")
        for result in store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter):
            print(f"  {result['id']} score={result['score']:.4f} doc_id={result['metadata']['doc_id']}")


if __name__ == "__main__":
    main()
