import streamlit as st
import os
from backend.ai_architect import AIArchitect
from backend.fabrication_layout import FabricationLayout

st.set_page_config(page_title="Quantum Chip Architect", layout="wide")

st.title("AI-Assisted Superconducting Quantum Chip Layout Synthesis")
st.markdown("Generate realistic, multi-layer GDSII fabrication layouts from natural language prompts.")

# Sidebar for Prompt Input
st.sidebar.header("Architecture Prompt")
prompt = st.sidebar.text_area(
    "Describe your desired chip architecture:",
    value="Design a scalable low-noise chip for quantum error correction with 24 qubits",
    height=150
)

if st.sidebar.button("Generate Architecture"):
    with st.spinner("AI Architect is analyzing prompt and inferring constraints..."):
        architect = AIArchitect()
        spec = architect.analyze_prompt(prompt)
        
    st.sidebar.success("Architecture Spec Generated!")
    
    # Layout Generation
    with st.spinner("Synthesizing GDSII geometry and rendering..."):
        layout_engine = FabricationLayout(spec)
        gds_path, png_path, svg_path, metadata = layout_engine.generate()
        
    # Main Display Area
    st.markdown("---")
    
    col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
    with col_metrics1:
        st.metric("Qubits", spec['num_qubits'])
    with col_metrics2:
        st.metric("Topology", spec['topology'].replace('-', ' ').title())
    with col_metrics3:
        st.metric("Technology Preset", spec['preset'])
    with col_metrics4:
        st.metric("Routing Density", spec['density'].title())
        
    st.markdown("---")
        
    col1, col2 = st.columns([1.2, 2])
    
    with col1:
        st.subheader("🤖 AI Architect Analysis")
        st.info(spec['engineering_notes'], icon="🧠")
        
        with st.expander("📌 Design Constraints", expanded=True):
            st.markdown("**Hard Constraints**")
            for hc in spec['hard_constraints']:
                st.markdown(f"- {hc}")
            st.markdown("**Soft Constraints**")
            for sc in spec['soft_constraints']:
                st.markdown(f"- {sc}")
                
        with st.expander("⚙️ Fabrication Metadata", expanded=False):
            st.json(metadata)
        
        st.markdown("### 💾 Export Layout")
        if os.path.exists(gds_path) and os.path.exists(svg_path) and os.path.exists(png_path):
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                with open(gds_path, "rb") as f:
                    st.download_button("GDSII", f, file_name="chip_layout.gds", mime="application/octet-stream", use_container_width=True)
            with d_col2:
                with open(svg_path, "rb") as f:
                    st.download_button("SVG", f, file_name="chip_layout.svg", mime="image/svg+xml", use_container_width=True)
            with d_col3:
                with open(png_path, "rb") as f:
                    st.download_button("PNG", f, file_name="chip_layout.png", mime="image/png", use_container_width=True)
        
    with col2:
        st.subheader("🔬 Layout Preview")
        if os.path.exists(png_path):
            # A stylized container for the image
            st.markdown(
                """
                <style>
                .img-container {
                    border: 2px solid #333;
                    border-radius: 10px;
                    padding: 5px;
                    background-color: #050510;
                }
                </style>
                """, unsafe_allow_html=True
            )
            st.image(png_path, use_container_width=True, output_format="PNG")

else:
    # Display a placeholder welcome screen
    st.info("Enter a prompt in the sidebar and click 'Generate Architecture' to synthesize a layout.")
    st.markdown("### Examples")
    st.markdown("- *\"Design a scalable low-noise chip for quantum error correction with 64 qubits\"*")
    st.markdown("- *\"Create a heavy-hex layout IBM-style with 24 qubits\"*")
    st.markdown("- *\"I need a sparse modular research prototype with 16 qubits\"*")
