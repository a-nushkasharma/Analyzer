from __future__ import annotations
import json
from typing import Any, Dict, List
from rag_store import Retriever
from utils import save_json
from llm1_api import LLM1Client
from llm2_api import LLM2Client
from langchain.schema import Document

class Orchestrator:
    def __init__(self, retriever: Retriever):
        self.llm1 = LLM1Client()
        self.llm2 = LLM2Client()
        self.rag = retriever

    def run_phased(self, contract_code: str, contract_id: str = None) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        if contract_id is None:
            contract_id = "default_contract_id"

        # Phase 0: Ensure contract is indexed in RAG 
        if contract_id not in self.rag.registry._store:
            print(f" Contract ID '{contract_id}' not in RAG store. Indexing now...")
            self.rag.index_contract(contract_id, contract_code)
            print("✅ Contract indexed in RAG store.")

        #  Phase 1: Initial analysis 
        print("🚀 Starting Phase 1: Initial LLM analysis...")
        try:
            results["phase1"] = {
                "llm1": self.llm1.analyze_contract(contract_code, phase=1),
                "llm2": self.llm2.analyze_contract(contract_code, phase=1)
            }
            print("Phase 1 LLM1 output:", results["phase1"]["llm1"])
            print("Phase 1 LLM2 output:", results["phase1"]["llm2"])
            print("✅ Phase 1 completed successfully.")
        except Exception as e:
            print(f"❌ Error in Phase 1: {e}")
            results["phase1"] = {"llm1": {}, "llm2": {}}

        #  Phase 2: Cross verification with RAG 
        print("\n🚀 Starting Phase 2: Cross verification with RAG context...")
        try:
            rag_context = self.rag.retrieve(contract_id=contract_id, query=contract_code)
            print("RAG context chunks:", rag_context)

            results["phase2"] = {
                "llm1_on_llm2": self.llm1.analyze_contract(
                    contract_code,
                    phase=2,
                    context={
                        "counterparty_report": results["phase1"]["llm2"], 
                        "contract_snippets": rag_context
                    }
                ),
                "llm2_on_llm1": self.llm2.analyze_contract(
                    contract_code,
                    phase=2,
                    context={
                        "counterparty_report": results["phase1"]["llm1"], 
                        "contract_snippets": rag_context
                    }
                )
            }
            print("Phase 2 LLM1_on_LLM2 output:", results["phase2"]["llm1_on_llm2"])
            print("Phase 2 LLM2_on_LLM1 output:", results["phase2"]["llm2_on_llm1"])
            print("✅ Phase 2 completed successfully.")
        except Exception as e:
            print(f"❌ Error in Phase 2: {e}")
            results["phase2"] = {"llm1_on_llm2": {}, "llm2_on_llm1": {}}

        #  Phase 3: Final confirmation/dispute 
        print("\n🚀 Starting Phase 3: Final confirmation/dispute...")
        try:
            results["phase3"] = {
                "llm1_on_llm2": self.llm1.analyze_contract(
                    contract_code,
                    phase=3,
                    context={"other_findings": results["phase2"]["llm2_on_llm1"]}
                ),
                "llm2_on_llm1": self.llm2.analyze_contract(
                    contract_code,
                    phase=3,
                    context={"other_findings": results["phase2"]["llm1_on_llm2"]}
                )
            }
            print("Phase 3 LLM1_on_LLM2 output:", results["phase3"]["llm1_on_llm2"])
            print("Phase 3 LLM2_on_LLM1 output:", results["phase3"]["llm2_on_llm1"])
            print("✅ Phase 3 completed successfully.")
        except Exception as e:
            print(f"❌ Error in Phase 3: {e}")
            results["phase3"] = {"llm1_on_llm2": {}, "llm2_on_llm1": {}}

        # Build final report 
        print("\n🚀 Building final report...")
        try:
            results["final_report"] = self.build_final_report(results)
            save_json(results["final_report"], "outputs/report.json")
            print("✅ Final report generated and saved to outputs/report.json")
        except Exception as e:
            print(f"❌ Error building final report: {e}")
            results["final_report"] = {"final_findings": []}

        return results

    def build_final_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        confirmed_vulnerabilities: List[Dict[str, Any]] = []
        disputed_vulnerabilities: List[Dict[str, Any]] = []

        # 1. Aggregation of detailed findings from Phase 1 for easy lookup
        phase1_findings = {}
        for finding in results.get("phase1", {}).get("llm1", []) + results.get("phase1", {}).get("llm2", []):
            if finding and "id" in finding:
                if finding["id"] not in phase1_findings or finding["confidence"] > phase1_findings[finding["id"]]["confidence"]:
                    phase1_findings[finding["id"]] = finding

        # 2. Processing of final decisions from Phase 3
        phase3_results = results.get("phase3", {}).get("llm1_on_llm2", []) + results.get("phase3", {}).get("llm2_on_llm1", [])
        processed_ids = set()

        for entry in phase3_results:
            entry_id = entry.get("id")
            if not entry_id or entry_id in processed_ids:
                continue
            
            processed_ids.add(entry_id)
            original_finding = phase1_findings.get(entry_id, {})
            stance = entry.get("stance", "unknown").lower()

            vulnerability_details = {
                "status": stance,
                "type_of_error": original_finding.get("title", "N/A"),
                "confidence": entry.get("confidence"),
                "code_snippet": original_finding.get("evidence"),
                "evidence_rationale": f"Final Reason: {entry.get('reason')} | Initial Rationale: {original_finding.get('rationale')}",
                "recommendation_suggested_fix": original_finding.get("recommendation")
            }

            if stance == "confirm":
                confirmed_vulnerabilities.append(vulnerability_details)
            elif stance == "dispute":
                disputed_vulnerabilities.append(vulnerability_details)

        # 3. Assembling the summary report
        summary_report = {}
        if not confirmed_vulnerabilities and not disputed_vulnerabilities:
            summary_report["status"] = "No vulnerable section found"
        else:
            summary_report = {
                "confirmed_vulnerabilities": confirmed_vulnerabilities,
                "disputed_vulnerabilities": disputed_vulnerabilities
            }
            
        # 4. Assembling the final report without a circular reference
        return {
            "summary_report": summary_report,
            "detailed_llm_analysis": {
                "phase1": results.get("phase1"),
                "phase2": results.get("phase2"),
                "phase3": results.get("phase3")
            }
        }

# Quick test block to ensure import works
if __name__ == "__main__":
    print("Orchestrator.py loaded correctly")