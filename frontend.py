import streamlit as st
import json
import os
import time
from orchestrator import Orchestrator
from mock_analyzer import MockAnalyzer

#will be removed when API is wired
class DummyRetriever:
    def retrieve(self, *args, **kwargs):
        return ["dummy snippet"]

    def index_contract(self, contract_id, code):
        pass

st.set_page_config(page_title="Smart Contract Vulnerability Analyzer", layout="wide")
st.title("🔎 Smart Contract Vulnerability Analyzer")
st.write("Upload a Solidity contract and analyze it for potential vulnerabilities.")

# File uploader
uploaded_file = st.file_uploader("Upload Solidity Smart Contract (.sol)", type=["sol"])

if uploaded_file is not None:
    # Save uploaded contract to temp file
    os.makedirs("uploads", exist_ok=True)
    contract_path = f"uploads/{uploaded_file.name}"
    with open(contract_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Uploaded: {uploaded_file.name}")

    # Show contract code
    with st.expander("View Contract Code"):
        st.code(uploaded_file.getvalue().decode("utf-8"), language="solidity")

    if st.button("Run Vulnerability Analysis 🚀"):
        contract_code = uploaded_file.getvalue().decode("utf-8")

        # Dummy retriever(to be removed when wired )
        dummy_retriever = DummyRetriever()
        orch = Orchestrator(retriever=dummy_retriever, analyzer=MockAnalyzer(dummy_retriever))

        # Temporary status message container
        status = st.empty()

        # ------------------ Phase 1 ------------------
        status.info("🔹 Phase 1: Ingesting contract...")
        with st.spinner("Indexing contract..."):
            contract_id = orch.analyzer.ingest_contract(contract_code)
            time.sleep(1)
        status.empty()

        # ------------------ Phase 2 ------------------
        status.info("🔹 Phase 2: Running full contract analysis...")
        with st.spinner("Analyzing with LLM1 and LLM2..."):
            l1_findings = orch._call_full_analysis(orch.llm1, contract_code)
            l2_findings = orch._call_full_analysis(orch.llm2, contract_code)
            time.sleep(1)
        status.empty()

        # ------------------ Phase 3 ------------------
        status.info("🔹 Phase 3: Cross-verifying findings...")
        with st.spinner("Cross-verifying vulnerabilities..."):
            l1_on_l2, l2_on_l1 = [], []
            for item in l2_findings:
                snippets = dummy_retriever.retrieve(contract_id, query=item.get("evidence", item.get("title", "")))
                l1_on_l2.extend(orch._call_verify(orch.llm1, item, snippets))
            for item in l1_findings:
                snippets = dummy_retriever.retrieve(contract_id, query=item.get("evidence", item.get("title", "")))
                l2_on_l1.extend(orch._call_verify(orch.llm2, item, snippets))
            time.sleep(1)
        status.empty()

        # ------------------ Phase 4 ------------------
        status.info("🔹 Phase 4: Confirming/disputing verifications...")
        with st.spinner("Generating consensus..."):
            l1_confirms, l2_confirms = [], []
            for item in l2_on_l1:
                snippets = dummy_retriever.retrieve(contract_id, query=item.get("reason", item.get("original_title", "")))
                l1_confirms.extend(orch._call_confirm(orch.llm1, item, snippets))
            for item in l1_on_l2:
                snippets = dummy_retriever.retrieve(contract_id, query=item.get("reason", item.get("original_title", "")))
                l2_confirms.extend(orch._call_confirm(orch.llm2, item, snippets))
            time.sleep(1)
        status.empty()

        # ------------------ Phase 5 ------------------
        status.info("🔹 Phase 5: Generating final consolidated report...")
        with st.spinner("Building final report..."):
            phase3_results = l1_on_l2 + l2_on_l1
            phase4_results = l1_confirms + l2_confirms
            final_output = orch.phase5_final_report(
                contract_id=contract_id,
                phase3_verifications=phase3_results,
                phase4_consensus=phase4_results
            )

            os.makedirs("outputs", exist_ok=True)
            final_report_path = "outputs/final_report.json"
            with open(final_report_path, "w") as f:
                json.dump(final_output, f, indent=2)
            time.sleep(1)
        status.empty()

        # ------------------ Results ------------------
        st.header("📊 Vulnerabilities Detected")
        vulns = final_output["final_report"]["vulnerabilities"]
        stats = final_output["final_report"]["stats"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Detected", stats["total_detected"])
        col2.metric("Confirmed", stats["confirmed"])
        col3.metric("Disputed", stats["disputed"])
        col4.metric("Needs More Evidence", stats["needs_more_evidence"])

        for v in vulns:
            with st.expander(f"{v['title']} ({v['consensus']})"):
                st.markdown(f"**Category:** {v.get('category', 'N/A')}")
                st.markdown(f"**Severity:** {v.get('severity', 'N/A')}")
                st.markdown(f"**Confidence:** {v.get('confidence', 'N/A')}")
                st.markdown(f"**Affected Components:** {', '.join(v.get('affected_components', []))}")
                st.markdown(f"**Evidence/Rationale:** {v.get('rationale', 'N/A')}")
                st.markdown(f"**Recommendation:** {v.get('recommendation', 'N/A')}")
                st.markdown(f"**Related References:** {', '.join(v.get('related_refs', []))}")

        # Download button
        st.download_button(
            label="⬇️ Download Final Report (JSON)",
            data=json.dumps(final_output, indent=2),
            file_name="final_report.json",
            mime="application/json"
        )

        st.success("✅ Analysis complete! You can review the report above.")
