import os
import json
from dotenv import load_dotenv
from llm1_api import LLM1Client
from llm2_api import LLM2Client
from util import SimpleRAG

load_dotenv()
class Analyzer:
    """
    Multi-phase analyzer:
    1. Both LLMs analyze the raw smart contract.
    2. Each LLM re-analyzes using the other's output + RAG context.
    3. Each LLM validates or disputes the other's Phase 2 results.
    Final JSON report consolidates everything.
    """

    def __init__(self):
        self.llm1 = LLM1Client(model="gpt-4o-mini")
        self.llm2 = LLM2Client(model="gemini-1.5-pro")
        self.rag = SimpleRAG()

    def analyze_contract(self, contract_code: str) -> dict:
        contract_id = self.ingest_contract(contract_code)

        #Phase 1: Independent analysis
        print("🚀 Starting Phase 1: Initial LLM analysis...")
        llm1_initial = self.llm1.analyze_contract(contract_code, phase=1)
        llm2_initial = self.llm2.analyze_contract(contract_code, phase=1)

        #Phase 2: Cross-review with RAG 
        print("\n🚀 Starting Phase 2: Cross verification with RAG context...")
        rag_context = self.rag.retrieve(contract_id)

        llm1_cross = self.llm1.analyze_contract(
            contract_code,
            phase=2,
            context={
                "counterparty_report": llm2_initial,
                "contract_snippets": rag_context
            }
        )

        llm2_cross = self.llm2.analyze_contract(
            contract_code,
            phase=2,
            context={
                "counterparty_report": llm1_initial,
                "contract_snippets": rag_context
            }
        )

        #Phase 3: Confirm / Dispute 
        print("\n🚀 Starting Phase 3: Final confirmation/dispute...")
        llm1_final = self.llm1.analyze_contract(
            contract_code,
            phase=3,
            context={"other_findings": llm2_cross}
        )

        llm2_final = self.llm2.analyze_contract(
            contract_code,
            phase=3,
            context={"other_findings": llm1_cross}
        )

        #Consolidate Report 
        print("\n🚀 Building final report...")
        report = {
            "contract_id": contract_id,
            "phase1": {"llm1": llm1_initial, "llm2": llm2_initial},
            "phase2": {"llm1": llm1_cross, "llm2": llm2_cross},
            "phase3": {"llm1": llm1_final, "llm2": llm2_final},
        }
        return report

    def ingest_contract(self, contract_code: str) -> str:
        #Hash + store contract in RAG, return contract_id
        import hashlib

        contract_id = hashlib.sha256(contract_code.encode()).hexdigest()[:12]
        self.rag.add(contract_id, contract_code)
        return contract_id


if __name__ == "__main__":
    analyzer = Analyzer()
    sample_code = """
    pragma solidity ^0.8.0;
    contract Test {
        mapping(address => uint) public balances;
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
        function withdraw(uint amount) public {
            require(balances[msg.sender] >= amount, "Not enough funds");
            (bool ok,) = msg.sender.call{value: amount}("");
            require(ok, "Transfer failed");
            balances[msg.sender] -= amount;
        }
    }
    """
    result = analyzer.analyze_contract(sample_code)
    print("\n--- FINAL REPORT ---")
    print(json.dumps(result, indent=2))