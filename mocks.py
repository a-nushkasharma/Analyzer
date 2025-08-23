import json
import re
from typing import List

class MockLLM:
    def __init__(self, name="mock"):
        self.name = name

    def call(self, prompt: str):
        prompt_lower = prompt.lower()

        # Phase 2: Full analysis
        if "full contract code" in prompt_lower or "you are a smart contract security auditor" in prompt_lower:
            return json.dumps([{
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
            }])

        # Phase 3: Cross-verify
        elif "counterparty report" in prompt_lower or "counterparty_report" in prompt_lower:
            return json.dumps([{
                "id": "vuln-reentrancy",
                "original_title": "Reentrancy via low-level call",
                "valid": True,
                "confidence": 0.9,
                "decision": "confirm",
                "reason": "Snippets show external call before state update",
                "corrected_category": "SWC-107",
                "corrected_severity": "high",
                "extra_evidence_needed": None
            }])

        # Phase 4: Confirm/dispute
        elif "verification_item" in prompt_lower:
            try:
                # extract the verification_item JSON from the prompt
                start = prompt.find("{")
                end = prompt.rfind("}") + 1
                verification_item = json.loads(prompt[start:end])
            except Exception:
                verification_item = {}

            evidence_text = "\n".join(prompt.split("Relevant contract snippets:")[1:]).lower() if "Relevant contract snippets:" in prompt else ""
    
    # simple heuristic: confirm if snippet contains key terms
            keywords = ["call{", ".call{", "delegatecall", "reentrancy", "transfer("]
            stance = "confirm" if any(kw in evidence_text for kw in keywords) else "dispute"
            confidence = 0.9 if stance == "confirm" else 0.4
            reason = "Snippets show external call or reentrancy pattern" if stance == "confirm" else "No clear evidence in snippets"

            out = [{
                "id": verification_item.get("id", "vuln-1"),
                 "stance": stance,
                 "confidence": confidence,
                "reason": reason,
                 "what_is_missing": None if stance == "confirm" else "fetch related function or storage variable declarations"
            }]
            return json.dumps(out)

        # default empty
        return json.dumps([])

