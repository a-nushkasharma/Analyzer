from __future__ import annotations
import hashlib
import re
from typing import List, Dict, Any
from langchain.schema import Document

class ContractRegistry:
    def __init__(self):
        # _store maps contract_id -> List[Document]
        self._store: Dict[str, List[Document]] = {}

    def put(self, contract_id: str, docs: List[Document]):
        self._store[contract_id] = docs

    def get(self, contract_id: str) -> List[Document]:
        return self._store.get(contract_id, [])

class Retriever:
    #Indexes contract (once) and supports snippet retrieval by query.
    
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.registry = ContractRegistry()

    def _hash(self, s: str) -> str:
        import hashlib
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    def _split_by_function(self, code: str) -> List[str]:
        # Split by 'function' token — keeps semantic units
        parts = re.split(r"(?=\bfunction\s+\w+\s*\()", code, flags=re.IGNORECASE)
        out = [p.strip() for p in parts if p.strip()]
        if len(out) == 0:
            return [code]
        return out

    def index_contract(self, contract_id: str, contract_code: str) -> str:
        # Split contract into chunks
        chunks = self._split_by_function(contract_code)
        # Convert each chunk to a Document
        docs = [Document(page_content=chunk) for chunk in chunks]
        self.registry.put(contract_id, docs)
        return contract_id

    def retrieve(self, contract_id: str, query: str, k: int = 4) -> List[str]:
        rec_list = self.registry.get(contract_id)
        if not rec_list:
            return []

        # Extract text content from Documents
        texts = [getattr(doc, "page_content", getattr(doc, "content", "")) for doc in rec_list]

        # naive scoring: keyword hits + overlap with query tokens
        q = query.lower()
        scored = []
        keywords = [
            "call{", ".call{", "delegatecall", "selfdestruct", "tx.origin",
            "owner", "onlyOwner", "reentrancy", "require", "revert", "transfer("
        ]
        for text in texts:
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 2
            for tok in set(q.split()):
                score += text.lower().count(tok)
            scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [c for s, c in scored[:k] if s > 0]
        return top or texts[:k]
    
    def retrieve(self, contract_id: str, query: str, k: int = 4) -> List[str]:
        rec_list = self.registry.get(contract_id)
        if not rec_list:
            print(f"⚠️ Contract ID '{contract_id}' not found in registry.")
            return []

        texts = [getattr(doc, "page_content", getattr(doc, "content", "")) for doc in rec_list]

    # Scoring by keywords + query overlap
        q_tokens = set(query.lower().split())
        keywords = [
            "call{", ".call{", "delegatecall", "selfdestruct", "tx.origin",
            "owner", "onlyOwner", "reentrancy", "require", "revert", "transfer("
        ]
        scored = []
        for text in texts:
            score = sum(text.lower().count(kw) * 2 for kw in keywords)
            score += sum(text.lower().count(tok) for tok in q_tokens)
            scored.append((score, text))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [c for s, c in scored[:k] if s > 0]

    # Debug info
        print(f"🔹 RAG retrieved {len(top)} chunks for contract '{contract_id}':")
        for i, chunk in enumerate(top, 1):
            snippet_preview = chunk[:80].replace("\n", " ") + "..."
            print(f"   [{i}] {snippet_preview}")

        return top or texts[:k]  # fallback to first k if none scored

