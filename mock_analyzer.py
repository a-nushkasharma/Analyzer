import uuid

class MockAnalyzer:
    def __init__(self, retriever=None):
        self.contracts = {}
        self.retriever = retriever

    def ingest_contract(self, code: str) -> str:
        """Pretend to store the contract and return an ID"""
        contract_id = str(uuid.uuid4())
        self.contracts[contract_id] = code
        print(f"[MockAnalyzer] Ingested contract {contract_id[:8]}...")

        if self.retriever: 
            self.retriever.index_contract(contract_id, code)

        return contract_id

    def extract_functions(self, contract_id: str):
        """Pretend to parse functions (static output for now)"""
        return [
            {"name": "deposit", "code": "function deposit() public payable {}"},
            {"name": "withdraw", "code": "function withdraw(uint amount) public {}"}
        ]

    def analyze_function(self, function):
        """Pretend analysis with mock vulnerability flags"""
        return {
            "function": function["name"],
            "issues": ["reentrancy risk"] if function["name"] == "withdraw" else []
        }
