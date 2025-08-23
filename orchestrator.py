from __future__ import annotations
import json
from typing import Any, List, Dict
from rag_store import Retriever
#from analyzer import Analyzer (for wiring real APIs)
from mock_analyzer import MockAnalyzer
from utils import coerce_json_list, save_json, load_prompt
from mocks import MockLLM
from final_report import generate_final_report

class Orchestrator:
    """Orchestrates 4-phase flow:
    1) Ingest -> index contract once
    2) Full analysis by LLM1 & LLM2 (single full-contract prompt)
    3) Cross-verify: LLM1 verifies LLM2's findings and vice versa using RAG snippets
    4) Confirm/dispute: exchange verification results and confirm/dispute (RAG snippets)
    """

    def __init__(self, retriever: Retriever, analyzer=None, llm1=None, llm2=None):
        self.retriever = retriever
        # allow injection of either a real Analyzer or MockAnalyzer
        self.analyzer =analyzer or MockAnalyzer(self.retriever) #change with analyzer
        self.llm1 = llm1 or MockLLM("llm1-mock")
        self.llm2 = llm2 or MockLLM("llm2-mock")
        # load prompts
        self.analysis_prompt = load_prompt("analysis_prompt")
        self.verify_prompt = load_prompt("cross_verify_prompt")
        self.confirm_prompt = load_prompt("confirm_dispute_prompt")

    def _call_full_analysis(self, llm, full_code: str) -> List[Dict]:
        prompt = (
            self.analysis_prompt.replace("{full_code}", full_code)
            if "{full_code}" in self.analysis_prompt
            else self.analysis_prompt + "\n\nFULL CONTRACT CODE:\n" + full_code
        )
        raw = llm.call(prompt)
        return coerce_json_list(raw)

    def _call_verify(self, llm, counterparty_item: Dict, snippets: List[str]) -> List[Dict]:
        prompt = self.verify_prompt.format(
            counterparty_report=json.dumps([counterparty_item], ensure_ascii=False),
            contract_snippets="\n\n".join(snippets),
        )
        raw = llm.call(prompt)
        return coerce_json_list(raw)

    def _call_confirm(self, llm, verification_item: Dict, snippets: List[str]) -> List[Dict]:
        prompt = self.confirm_prompt.format(
            verification_item=json.dumps(verification_item, ensure_ascii=False),
            contract_snippets="\n\n".join(snippets),
        )
        raw = llm.call(prompt)
        return coerce_json_list(raw)

    def run_phased(self, contract_code: str, k_verify: int = 4, outpath: str = "outputs/report.json") -> Dict[str, Any]:
        
        # 1) Ingest
        contract_id = self.analyzer.ingest_contract(contract_code)

        # 2) Full contract analysis (single send per LLM)
        l1_findings = self._call_full_analysis(self.llm1, contract_code)
        l2_findings = self._call_full_analysis(self.llm2, contract_code)

        # 3) Cross-verify using only RAG snippets
        l1_on_l2 = []
        for item in l2_findings:
            snippets = self.retriever.retrieve(
                contract_id, query=item.get("evidence", item.get("title", "")), k=k_verify
            )
            l1_on_l2.extend(self._call_verify(self.llm1, item, snippets))

        l2_on_l1 = []
        for item in l1_findings:
            snippets = self.retriever.retrieve(
                contract_id, query=item.get("evidence", item.get("title", "")), k=k_verify
            )
            l2_on_l1.extend(self._call_verify(self.llm2, item, snippets))

        # 4) Confirm/dispute: each LLM checks the verification decisions
        l1_confirms, l2_confirms = [], []
        for item in l2_on_l1:
            snippets = self.retriever.retrieve(
                contract_id, query=item.get("reason", item.get("original_title", "")), k=k_verify
            )
            l1_confirms.extend(self._call_confirm(self.llm1, item, snippets))

        for item in l1_on_l2:
            snippets = self.retriever.retrieve(
                contract_id, query=item.get("reason", item.get("original_title", "")), k=k_verify
            )
            l2_confirms.extend(self._call_confirm(self.llm2, item, snippets))

        # Consolidate results
        final = {
            "contract_id": contract_id,
            "phase2_full_analysis": {"llm1_findings": l1_findings, "llm2_findings": l2_findings},
            "phase3_verifications": {"llm1_on_llm2": l1_on_l2, "llm2_on_llm1": l2_on_l1},
            "phase4_consensus_checks": {"llm1_confirms": l1_confirms, "llm2_confirms": l2_confirms},
        }
        save_json(final, outpath)
        return final

    def phase5_final_report(self, contract_id, phase3_verifications, phase4_consensus):
        """Build final consolidated report by merging verifications and consensus results."""
        final_vulns = []
        stats = {"total_detected": 0, "confirmed": 0, "disputed": 0, "needs_more_evidence": 0}

        # Index consensus by ID for easy lookup
        consensus_map = {item["id"]: item for item in (phase4_consensus or [])}

        for v in (phase3_verifications or []):
            vid = v["id"]
            consensus_item = consensus_map.get(vid)

            final_entry = {
                "id": vid,
                "title": v.get("original_title"),
                "category": v.get("corrected_category"),
                "severity": v.get("corrected_severity"),
                "confidence": v.get("confidence"),
                "evidence": v.get("reason"),
                "rationale": v.get("reason"),
                "affected_components": v.get("affected_components", []),
                "recommendation": v.get("recommendation"),
                "related_refs": v.get("related_refs", []),
                "consensus": consensus_item["stance"] if consensus_item else "unknown"
            }
            final_vulns.append(final_entry)

            # Update stats
            stats["total_detected"] += 1
            if consensus_item:
                if consensus_item["stance"] == "confirm":
                    stats["confirmed"] += 1
                elif consensus_item["stance"] == "dispute":
                    stats["disputed"] += 1
                elif consensus_item["stance"] == "needs-more-evidence":
                    stats["needs_more_evidence"] += 1

        return {
            "contract_id": contract_id,
            "final_report": {"vulnerabilities": final_vulns, "stats": stats}
        }


if __name__ == "__main__":
    sample = """...vault contract here..."""
    retriever = Retriever()
    orch = Orchestrator(retriever)

    # Run Phases 1–4
    result = orch.run_phased(sample)

    # Run Phase 5 (Final consolidation)
    phase3_results = result["phase3_verifications"]["llm1_on_llm2"] + result["phase3_verifications"]["llm2_on_llm1"]
    phase4_results = result["phase4_consensus_checks"]["llm1_confirms"] + result["phase4_consensus_checks"]["llm2_confirms"]

    print("\n[Orchestrator] Generating final consolidated report...")
    generate_final_report("outputs/report.json", "outputs/final_report.json")
    final_output = orch.phase5_final_report(
        contract_id=result["contract_id"],
        phase3_verifications=phase3_results,
        phase4_consensus=phase4_results
    )

    with open("outputs/final_report.json", "w") as f:
        json.dump(final_output, f, indent=2)

    print("Final report written to outputs/final_report.json")

