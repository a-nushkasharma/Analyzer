import streamlit as st
import json
import os
import time
from orchestrator import Orchestrator
from rag_store import Retriever

st.set_page_config(page_title="Smart Contract Vulnerability Analyzer", layout="wide")
st.title("🔎 Smart Contract Vulnerability Analyzer")
st.write("Upload a Solidity contract and analyze it for potential vulnerabilities using a multi-phase, multi-LLM approach.")

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

        # real retriever + orchestrator
        retriever = Retriever()
        orch = Orchestrator(retriever=retriever)

        # Status container
        status = st.empty()

        # Running all phases
        status.info("🚀 Running full multi-phase analysis... This may take a moment.")
        with st.spinner("Analyzing across multiple LLMs and phases..."):
            result = orch.run_phased(contract_code)
            time.sleep(1)
        status.empty()

        # Display Results 
        st.header("📊 Final Analysis Report")
        
        final_report = result.get("final_report", {})
        summary = final_report.get("summary_report", {})

        if summary.get("status") == "No vulnerable section found":
            st.success("✅ No vulnerable sections found in the contract.")
        else:
            confirmed = summary.get("confirmed_vulnerabilities", [])
            disputed = summary.get("disputed_vulnerabilities", [])
            all_vulns = confirmed + disputed

            # Calculate stats based on the structure
            stats = {
                "total_detected": len(all_vulns),
                "confirmed": len(confirmed),
                "disputed": len(disputed),
            }

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Detected", stats["total_detected"])
            col2.metric("Confirmed", stats["confirmed"])
            col3.metric("Disputed", stats["disputed"])

            st.markdown("---")
            
            if not all_vulns:
                st.warning("Analysis complete, but no specific findings were finalized.")
            else:
                for v in all_vulns:
                    # Use a title with the error type and a colored status
                    status_color = "green" if v.get('status') == "confirm" else "red"
                    expander_title = f"**{v.get('type_of_error', 'N/A')}** (`Status: {v.get('status', 'N/A').upper()}`)"
                    
                    with st.expander(expander_title):
                        st.markdown(f"**Confidence:** `{v.get('confidence', 'N/A')}`")
                        st.markdown(f"**Evidence/Rationale:**")
                        st.info(v.get('evidence_rationale', 'N/A'))
                        st.markdown(f"**Recommendation/Suggested Fix:**")
                        st.success(v.get('recommendation_suggested_fix', 'N/A'))
                        st.markdown(f"**Code Snippet (where issue occurs):**")
                        st.code(v.get('code_snippet', 'Not available'), language="solidity")

        # The download button
        st.download_button(
            label="⬇️ Download Full Report (JSON)",
            data=json.dumps(final_report, indent=2),
            file_name="full_analysis_report.json",
            mime="application/json",
        )

        st.success("✅ Analysis complete! You can review the report above.")