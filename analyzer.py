import json
import re
from typing import List

class MockLLM:
    
    def __init__(self, name: str):
        self.name = name

    def call(self, prompt: str) -> str:
        if "FULL CONTRACT CODE" in prompt or "FULL CONTRACT" in prompt or "You are a smart contract security auditor" in prompt:
            findings = []
            # heuristics
            if ".call{" in prompt or "call{" in prompt or ".call(" in prompt:
                findings.append({
                    "id": "vuln-reentrancy",
                    "title": "Reentrancy via low-level call",
                    "category": "SWC-107",
                    "severity": "high",
                    "confidence": 0.85,
                    "evidence": "external call via .call{value:...} before state update (withdraw)",
                    "rationale": "State change after external call enables reentrancy",
                    "affected_components": ["withdraw"],
                    "recommendation": "Move state update before external call or use ReentrancyGuard",
                    "related_refs": ["SWC-107"]
                })
            if "tx.origin" in prompt:
                findings.append({
                    "id": "vuln-txorigin",
                    "title": "Use of tx.origin for authentication",
                    "category": "SWC-115",
                    "severity": "medium",
                    "confidence": 0.75,
                    "evidence": "tx.origin used in an access check",
                    "rationale": "tx.origin is unsafe for auth checks",
                    "affected_components": ["auth functions"],
                    "recommendation": "Use msg.sender and proper role management",
                    "related_refs": ["SWC-115"]
                })
            return json.dumps(findings)
        if "Counterparty report" in prompt or "verifying another model" in prompt:
            # extract the JSON from the prompt if possible
            try:
                # crude parse
                s = prompt.find("Counterparty report (JSON):")
                payload = []
                if s != -1:
                    raw = prompt[s+len("Counterparty report (JSON):"):].strip()
                    start = raw.find("[")
                    end = raw.rfind("]")
                    if start != -1 and end != -1:
                        payload = json.loads(raw[start:end+1])
            except Exception:
                payload = []
            out = []
            for it in (payload or []):
                # simple logic: confirm items that have 'reentrancy' or 'call' in evidence
                evidence = (it.get("evidence") or "").lower()
                if "reentrancy" in evidence or "call" in evidence or "external call" in evidence:
                    out.append({
                        "id": it.get("id", "vuln-1"),
                        "original_title": it.get("title"),
                        "valid": True,
                        "confidence": 0.8,
                        "decision": "confirm",
                        "reason": "Snippet shows external call pattern matching reentrancy risk",
                        "corrected_category": it.get("category"),
                        "corrected_severity": it.get("severity"),
                        "extra_evidence_needed": None
                    })
                else:
                    out.append({
                        "id": it.get("id", "vuln-1"),
                        "original_title": it.get("title"),
                        "valid": False,
                        "confidence": 0.3,
                        "decision": "needs-more-evidence",
                        "reason": "No clear evidence in provided snippets",
                        "corrected_category": None,
                        "corrected_severity": None,
                        "extra_evidence_needed": "fetch related function or storage variable declarations"
                    })
            return json.dumps(out)
        # If it's a confirm/dispute prompt
        if "Prior verification item" in prompt or "Verification item:" in prompt:
            # return confirm for most things
            return json.dumps([{
                "id": "vuln-reentrancy",
                "stance": "confirm",
                "confidence": 0.85,
                "reason": "Evidence is sufficient in the snippet",
                "what_is_missing": None
            }])
        return json.dumps([])
