from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ContractRecord:
    contract_id: str
    original_code: str
    chunks: List[str] = field(default_factory=list)

class ContractRegistry:
    def __init__(self):
        self._store: Dict[str, ContractRecord] = {}

    def put(self, rec: ContractRecord):
        self._store[rec.contract_id] = rec

    def get(self, contract_id: str) -> ContractRecord:
        return self._store[contract_id]

class Retriever:
    """Indexes contract (once) and supports snippet retrieval by query.

    implementation for mocks/dev.
    when we wire embeddings,we'll swap to FAISS.
    """
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.registry = ContractRegistry()

    def _hash(self, s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    def _split_by_function(self, code: str) -> List[str]:
        # Split by 'function' token — keeps semantic units
        parts = re.split(r"(?=\bfunction\s+\w+\s*\()", code, flags=re.IGNORECASE)
        out = [p.strip() for p in parts if p.strip()]
        # keep header (pragma, imports, contract signature) as first chunk if present
        if len(out) == 0:
            return [code]
        return out

    def index_contract(self, contract_id: str, contract_code: str) -> str:
        chunks = self._split_by_function(contract_code)
        rec = ContractRecord(contract_id=contract_id, original_code=contract_code, chunks=chunks)
        self.registry.put(rec)
        return contract_id

    def retrieve(self, contract_id: str, query: str, k: int = 4) -> List[str]:
        rec = self.registry.get(contract_id)
        # naive scoring: keyword hits + overlap with query tokens
        q = query.lower()
        scored = []
        for ch in rec.chunks:
            score = 0
            keywords = ["call{", ".call{", "delegatecall", "selfdestruct", "tx.origin", "owner", "onlyOwner", "reentrancy", "require", "revert", "transfer("]
            for kw in keywords:
                if kw in ch:
                    score += 2
            for tok in set(q.split()):
                score += ch.lower().count(tok)
            scored.append((score, ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [c for s, c in scored[:k] if s > 0]
        return top or rec.chunks[:k]
