import sys
from rag_store import Retriever
from orchestrator import Orchestrator

USAGE = "python app.py <path-to-solidity-file>"

def main():
    if len(sys.argv) < 2:
        print(USAGE); return
    path = sys.argv[1]
    code = open(path, encoding="utf-8").read()
    retriever = Retriever()
    orchestrator = Orchestrator(retriever)
    result = orchestrator.run_phased(code)
    print("Result saved to outputs/report.json")
    import json; print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
