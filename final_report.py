import json
from pathlib import Path

def generate_final_report(report_path="outputs/report.json", final_path="outputs/final_report.json"):
    report_file = Path(report_path)
    final_file = Path(final_path)

    if not report_file.exists():
        print(f"[Error] Report file not found: {report_path}")
        return

    with open(report_file, "r") as f:
        data = json.load(f)

    final_findings = []

    # Gathers findings from LLM1 + LLM2 consensus stage
    if "phase3_verifications" in data:
        for side in ["llm1_on_llm2", "llm2_on_llm1"]:
            for entry in data["phase3_verifications"].get(side, []):
                final_findings.append({
                    "id": entry.get("id"),
                    "title": entry.get("original_title"),
                    "category": entry.get("corrected_category"),
                    "severity": entry.get("corrected_severity"),
                    "confidence": entry.get("confidence"),
                    "decision": entry.get("decision"),
                    "reason": entry.get("reason")
                })

    final_report = {
        "contract_id": data.get("contract_id"),
        "final_findings": final_findings
    }

    with open(final_file, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"[FinalReport] Saved final report to {final_file}")
    return final_report

if __name__ == "__main__":
    generate_final_report()
