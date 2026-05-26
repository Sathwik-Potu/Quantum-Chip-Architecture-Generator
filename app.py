import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

from utils.chip_engine import design_quantum_chip
from utils.quantum_circuit import run_circuit
from utils.chip_layout import draw_superconducting_chip, draw_schematic_chip

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantumChip AI",
    page_icon="⚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding-bottom:.75rem;
            border-bottom:1px solid #1e3a5c;margin-bottom:1rem">
  <div style="font-size:2.4rem;line-height:1">⚛</div>
  <div>
    <div style="font-size:1.8rem;font-weight:800;color:#d4eef8;letter-spacing:-.5px">
      QuantumChip <span style="color:#38a0c8">AI</span>
    </div>
    <div style="font-size:.88rem;color:#6a9ab8">
      Describe a chip — AI designs the full quantum architecture instantly
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Plotly dark theme ─────────────────────────────────────────────────────────
DARK      = dict(plot_bgcolor="#060e1e", paper_bgcolor="#060e1e",
                 font=dict(color="#9ec8e0", size=12))
DARK_AXIS = dict(gridcolor="#0d2040", zerolinecolor="#0d2040")

# ── Session state ─────────────────────────────────────────────────────────────
if "design" not in st.session_state:
    st.session_state.design = design_quantum_chip("4-qubit quantum processor")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "bot",
        "text": ("👋 I'm **QuantumChip AI**. Describe any quantum chip and I'll design the full "
                 "architecture — qubits, circuits, chip layout, and metrics — instantly.\n\n"
                 "**Try:** *Design a 4-qubit quantum processor* · "
                 "*8-qubit quantum AI accelerator* · "
                 "*16-qubit quantum cryptography chip*"),
        "data": None,
    }]

design = st.session_state.design

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⚛  Quantum Circuit",
    "🔲  Chip Layout",
    "💬  Design Chatbot",
    "📊  Dashboard",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — QUANTUM CIRCUIT
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    n_disp = min(design["n_qubits"], 8)
    st.markdown(f"### Quantum Circuit")
    st.caption(f"**{design['circuit']}** circuit · {n_disp} qubits · "
               f"{design['qubits_type']} · Fidelity {design['fidelity']}%")

    col_ctrl, col_info = st.columns([1, 3])
    with col_ctrl:
        shots   = st.slider("Measurement shots", 512, 8192, 2048, 256)
        run_btn = st.button("▶  Run Simulation", width='stretch')

    with col_info:
        st.markdown(f"""
        <div class="q-card" style="margin-top:0">
          <div class="q-card-title">Active Design</div>
          <div style="color:#d4eef8;font-weight:600;font-size:1rem">{design['prompt']}</div>
          <div class="q-card-sub">
            {design['n_qubits']} qubits · {design['circuit']} circuit ·
            T1 = {design['t1_us']} µs · {design['temp_mk']} mK
          </div>
        </div>""", unsafe_allow_html=True)

    design_key = design["prompt"] + str(design["n_qubits"])
    need_run   = (run_btn or
                  "qc_result" not in st.session_state or
                  st.session_state.get("qc_design_key") != design_key)
    if need_run:
        result = run_circuit(design, shots)
        st.session_state["qc_result"]     = result
        st.session_state["qc_design_key"] = design_key

    result     = st.session_state.get("qc_result", {})
    counts     = result.get("counts", {})
    shots_used = result.get("counts") and sum(result["counts"].values()) or shots

    # Circuit diagram
    st.markdown("#### Circuit Diagram")
    if result.get("real") and result.get("circuit_text"):
        st.code(result["circuit_text"], language="text")
    else:
        gate_colors = {"H":"#38a0c8","CNOT":"#34d399","RY":"#a78bfa",
                       "RZ":"#fb923c","CP":"#f472b6","M":"#4a7a9b"}
        ctype = design["circuit"]
        seq   = []
        if ctype == "Bell State":
            for i in range(0, n_disp-1, 2): seq += [("H",i,1),("CNOT",i,2),("CNOT",i+1,2)]
        elif ctype == "GHZ":
            seq.append(("H",0,1))
            for i in range(n_disp-1): seq += [("CNOT",i,i+2),("CNOT",i+1,i+2)]
        elif ctype == "Variational":
            for i in range(n_disp): seq.append(("RY",i,1))
            for i in range(n_disp-1): seq += [("CNOT",i,2),("CNOT",i+1,2)]
            for i in range(n_disp): seq.append(("RZ",i,3))
        else:
            for i in range(n_disp): seq.append(("H",i,1))
        ms = max(s[2] for s in seq) + 1
        for i in range(n_disp): seq.append(("M", i, ms))
        n_steps = ms + 2

        fc = go.Figure()
        for q in range(n_disp):
            fc.add_trace(go.Scatter(x=[0, n_steps], y=[q, q], mode="lines",
                line=dict(color="#0d2040", width=1.5), showlegend=False))
            fc.add_annotation(x=-.1, y=q, text=f"q{q}", showarrow=False,
                font=dict(size=10, color="#4a7a9b"), xanchor="right")
        for gate, qubit, step in seq:
            cc = gate_colors.get(gate, "#4a7a9b")
            fc.add_shape(type="rect", x0=step-.28, x1=step+.28,
                y0=qubit-.28, y1=qubit+.28, fillcolor=cc, line_color=cc, opacity=.9)
            fc.add_annotation(x=step, y=qubit, text=gate, showarrow=False,
                font=dict(size=9, color="white", family="monospace"))
        fc.update_layout(**DARK, height=max(200, n_disp*55),
            margin=dict(l=40, r=20, t=10, b=10),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                       range=[-.6, n_steps+.3], **DARK_AXIS),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                       range=[-.6, n_disp-.3], **DARK_AXIS))
        st.plotly_chart(fc, width='stretch')

    # Measurement results
    st.markdown("#### Measurement Results")
    if counts:
        top   = dict(sorted(counts.items(), key=lambda x: -x[1])[:16])
        total = sum(top.values())
        probs = [v / total for v in top.values()]

        fb = go.Figure(go.Bar(
            x=list(top.keys()), y=probs,
            marker=dict(color=probs,
                        colorscale=[[0,"#1a4a7c"],[0.5,"#2a7ab8"],[1,"#8ec8e8"]],
                        line=dict(color="#0d2040", width=1)),
            text=[f"{p:.1%}" for p in probs],
            textposition="outside",
            textfont=dict(color="#6a9ab8", size=10),
        ))
        fb.update_layout(**DARK,
            xaxis_title="Basis State", yaxis_title="Probability",
            yaxis=dict(tickformat=".0%", range=[0, max(probs)*1.3], **DARK_AXIS),
            xaxis=dict(showgrid=False, **DARK_AXIS),
            margin=dict(l=40, r=20, t=20, b=50), height=300)
        st.plotly_chart(fb, width='stretch')

        mc = max(counts, key=counts.get)
        for col, (title, val, sub) in zip(st.columns(4), [
            ("Dominant State", f"|{mc}⟩",              f"{counts[mc]/total:.1%} probability"),
            ("Unique States",  str(len(counts)),        "distinct outcomes"),
            ("Gate Fidelity",  f"{design['fidelity']}%","per gate"),
            ("T1 Coherence",   f"{design['t1_us']} µs", "decoherence time"),
        ]):
            with col:
                st.markdown(f"""
                <div class="q-card">
                  <div class="q-card-title">{title}</div>
                  <div class="q-card-value" style="font-size:1.3rem">{val}</div>
                  <div class="q-card-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — CHIP LAYOUT
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Quantum Processor Layout")
    st.caption(f"**{design['prompt']}** · {design['n_qubits']} qubits · "
               f"{design['qubits_type']} · {design['temp_mk']} mK")

    # View toggle
    view_col, info_col = st.columns([2, 4])
    with view_col:
        view = st.radio(
            "View",
            ["🔲 Fabricated", "📐 Schematic"],
            horizontal=True,
            label_visibility="collapsed",
        )

    if view == "🔲 Fabricated":
        st.caption("XMON transmons · CPW microwave routing · IDC couplers · λ/4 resonators · Hover for metadata")
        fig_chip = draw_superconducting_chip(design)
    else:
        st.caption("Schematic topology view · Qubit positions · Coupling graph")
        fig_chip = draw_schematic_chip(design)

    st.plotly_chart(fig_chip, use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True,
                            "modeBarButtonsToAdd": ["drawrect", "eraseshape"],
                            "displaylogo": False})

    # --- Architecture Summary ---
    from utils.chip_layout import generate_topology as _gt
    _qb, _cp = _gt(design["n_qubits"])
    _nq = len(_qb)
    _nc = len(_cp)

    # Compute connectivity degree per qubit
    _deg = {q: 0 for q in _qb}
    for a, b in _cp:
        _deg[a] += 1
        _deg[b] += 1
    _avg_deg = sum(_deg.values()) / max(len(_deg), 1)

    # Topology type label
    if _nq <= 4:
        _topo = "Linear Chain"
    elif _nq == 5:
        _topo = "Cross / Star"
    elif _nq <= 8:
        _topo = "2-Row Lattice"
    else:
        _cols = math.ceil(math.sqrt(_nq))
        _rows = math.ceil(_nq / _cols)
        _topo = f"{_rows}×{_cols} Surface-Code Grid"

    _bus_type = "Direct Ports" if _nq <= 6 else "Multiplexed Feedline"

    # KPI row
    for col, (title, val, sub) in zip(st.columns(5), [
        ("Qubits", str(_nq), "XMON Transmon"),
        ("Couplers", str(_nc), "IDC capacitive"),
        ("Resonators", str(_nq), "λ/4 readout"),
        ("Topology", _topo, f"Avg degree {_avg_deg:.1f}"),
        ("Readout Bus", _bus_type, f"{_nq} channels"),
    ]):
        with col:
            st.markdown(f"""
            <div class="q-card">
              <div class="q-card-title">{title}</div>
              <div class="q-card-value" style="font-size:1.2rem">{val}</div>
              <div class="q-card-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    col_spec, col_q = st.columns(2)

    with col_spec:
        st.markdown("#### Chip Specification")
        rows = "".join(
            f"<tr><td class='spec-label'>{k}</td>"
            f"<td class='spec-value'>{v}</td></tr>"
            for k, v in design["spec"].items())
        st.markdown(f"<table class='spec-table'>{rows}</table>",
                    unsafe_allow_html=True)

    with col_q:
        st.markdown("#### Qubit Fidelity")
        qcs = design["qubit_comps"]
        if qcs:
            fids   = [c["fidelity"] for c in qcs]
            names  = [c["name"]    for c in qcs]
            colors = [("#34d399" if f >= 99 else "#fbbf24" if f >= 97 else "#f87171")
                      for f in fids]
            fq = go.Figure(go.Bar(
                x=names, y=fids,
                marker=dict(color=colors, line=dict(color="#0d2040", width=1)),
                text=[f"{f:.1f}%" for f in fids],
                textposition="outside",
                textfont=dict(color="#6a9ab8", size=9),
            ))
            fq.add_hline(y=99, line_dash="dash", line_color="#34d399",
                annotation_text="99% target", annotation_font_color="#34d399")
            fq.update_layout(**DARK, height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis=dict(title="Fidelity (%)", range=[90, 100.5], **DARK_AXIS),
                xaxis=dict(showgrid=False, **DARK_AXIS))
            st.plotly_chart(fq, use_container_width=True)



# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — DESIGN CHATBOT
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Quantum Chip Design Chatbot")
    st.caption("Type your chip requirements → AI designs the full quantum architecture instantly.")

    # Chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div style="text-align:right;margin:.3rem 0">'
                f'<span class="chat-user">{msg["text"]}</span></div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="margin:.3rem 0">'
                f'<span class="chat-bot">{msg["text"]}</span></div>',
                unsafe_allow_html=True)
            if msg.get("data"):
                d   = msg["data"]
                cx  = d["complexity"]
                bcl = {"low":"badge-green","medium":"badge-yellow","high":"badge-red"}[cx]
                blb = {"low":"Low Complexity","medium":"Medium","high":"High Complexity"}[cx]
                spec_rows = "".join(
                    f"<tr><td class='spec-label'>{k}</td>"
                    f"<td class='spec-value'>{v}</td></tr>"
                    for k, v in d["spec"].items())
                comp_tags = " ".join(
                    f'<span class="chip-tag">{c["name"]}</span>'
                    for c in d["qubit_comps"])
                st.markdown(f"""
                <div style="background:#0a1826;border:1px solid #1e3a5c;
                            border-radius:14px;padding:1rem 1.2rem;
                            margin:.4rem 0 1rem 0;max-width:700px">
                  <div style="margin-bottom:.6rem;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                    <span class="status-badge {bcl}">{blb}</span>
                    <span style="font-size:.75rem;color:#3a6a8c">
                      ⚛ Circuit · 🔲 Chip Layout · 📊 Dashboard updated
                    </span>
                  </div>
                  <table class="spec-table">{spec_rows}</table>
                  <div style="margin-top:.8rem">
                    <div style="font-size:.7rem;color:#3a5a7c;font-weight:600;
                                letter-spacing:.5px;margin-bottom:5px">QUBITS</div>
                    {comp_tags}
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Describe your chip",
            placeholder="e.g. Design a 4-qubit quantum processor",
            label_visibility="visible",
        )
        send = st.form_submit_button("⚛  Design Chip", width='content')

    # Quick example buttons
    st.markdown("**Quick examples:**")
    ex_cols = st.columns(3)
    examples = [
        "4-qubit quantum processor",
        "8-qubit quantum AI accelerator",
        "16-qubit quantum computer",
        "2-qubit quantum communication",
        "8-qubit quantum cryptography chip",
        "32-qubit high performance chip",
    ]
    for i, ex in enumerate(examples):
        with ex_cols[i % 3]:
            if st.button(ex, key=f"ex_{i}", width='stretch'):
                user_input = ex
                send = True

    if send and user_input and user_input.strip():
        nd = design_quantum_chip(user_input.strip())
        st.session_state.design = nd
        st.session_state.pop("qc_result", None)

        st.session_state.chat_history.append(
            {"role": "user", "text": user_input.strip(), "data": None})
        st.session_state.chat_history.append({
            "role": "bot",
            "text": (f"✅ **{user_input.strip()}** designed successfully!  "
                     f"{nd['n_qubits']} qubits · {nd['qubits_type']} · "
                     f"Gate fidelity **{nd['fidelity']}%** · T1 = {nd['t1_us']} µs · "
                     f"{nd['temp_mk']} mK · {nd['err_correct']} error correction.  "
                     f"Check **Chip Layout** and **Quantum Circuit** tabs."),
            "data": nd,
        })
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Dashboard")
    st.caption(f"All metrics for: **{design['prompt']}**")

    qcs       = design["qubit_comps"]
    avg_fid   = np.mean([c["fidelity"] for c in qcs]) if qcs else design["fidelity"]
    total_pow = design["power_mw"]

    # KPI cards
    for col, (title, val, sub) in zip(st.columns(4), [
        ("Avg Gate Fidelity", f"{avg_fid:.1f}%",        "qubit quality"),
        ("T1 Coherence",      f"{design['t1_us']} µs",  "decoherence time"),
        ("Chip Power",        f"{total_pow} mW",         "total consumption"),
        ("Qubit Count",       str(design["n_qubits"]),   design["qubits_type"]),
    ]):
        with col:
            st.markdown(f"""
            <div class="q-card">
              <div class="q-card-title">{title}</div>
              <div class="q-card-value">{val}</div>
              <div class="q-card-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns(2)

    # Qubit fidelity over time
    with cl:
        st.markdown("##### Qubit Fidelity Over Time")
        np.random.seed(7)
        t_arr = np.linspace(0, 100, 60)
        palette = ["#8ec8e8","#34d399","#a78bfa","#fb923c","#f472b6","#fbbf24","#67e8f9","#c084fc"]
        ff = go.Figure()
        for qc_, col_ in zip(qcs[:6], palette):
            base = qc_["fidelity"] / 100
            vals = np.clip(base - np.abs(np.cumsum(np.random.randn(60)*0.0006)), 0.87, 1.0)
            ff.add_trace(go.Scatter(x=t_arr, y=vals*100, mode="lines",
                name=qc_["name"], line=dict(color=col_, width=1.8)))
        ff.add_hline(y=99, line_dash="dash", line_color="#34d399",
            annotation_text="99% target", annotation_font_color="#34d399")
        ff.update_layout(**DARK, height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Time (ns)", yaxis_title="Fidelity (%)",
            yaxis=dict(range=[87, 100.5], **DARK_AXIS),
            xaxis=dict(showgrid=False, **DARK_AXIS),
            legend=dict(font=dict(color="#6a9ab8", size=9),
                        bgcolor="#060e1e", orientation="h", y=-0.3))
        st.plotly_chart(ff, width='stretch')

    # Power gauge
    with cr:
        st.markdown("##### Power Consumption")
        mp = max(200, total_pow * 1.8)
        fg = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=total_pow,
            delta={"reference": mp*0.5, "valueformat": ".0f",
                   "increasing": {"color":"#f87171"},
                   "decreasing": {"color":"#34d399"}},
            number={"suffix": " mW", "font": {"size": 30, "color": "#d4eef8"}},
            gauge={
                "axis": {"range": [0, mp], "tickwidth": 1,
                         "tickcolor": "#0d2040",
                         "tickfont": {"color": "#4a7a9b"}},
                "bar":  {"color": "#38a0c8"},
                "bgcolor": "#060e1e",
                "borderwidth": 1, "bordercolor": "#0d2040",
                "steps": [
                    {"range": [0,       mp*.33], "color": "#021a10"},
                    {"range": [mp*.33,  mp*.66], "color": "#1a1500"},
                    {"range": [mp*.66,  mp],     "color": "#1a0404"},
                ],
                "threshold": {"line": {"color": "#f87171", "width": 3},
                              "thickness": .75, "value": mp*.66},
            }))
        fg.update_layout(height=280, paper_bgcolor="#060e1e",
            font=dict(color="#6a9ab8"), margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(fg, width='stretch')

    cbl, cbr = st.columns(2)

    # T1 coherence decay
    with cbl:
        st.markdown("##### T1 Coherence Decay")
        t_dec = np.linspace(0, design["t1_us"]*3, 200)
        fd = go.Figure()
        for qc_, col_ in zip(qcs[:4], palette):
            decay = np.exp(-t_dec / qc_["t1_us"]) * 100
            fd.add_trace(go.Scatter(x=t_dec, y=decay, mode="lines",
                name=qc_["name"], line=dict(color=col_, width=1.8)))
        fd.add_hline(y=36.8, line_dash="dash", line_color="#4a7a9b",
            annotation_text="1/e", annotation_font_color="#4a7a9b")
        fd.update_layout(**DARK, height=270,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Time (µs)", yaxis_title="Population (%)",
            yaxis=dict(range=[0, 105], **DARK_AXIS),
            xaxis=dict(showgrid=False, **DARK_AXIS),
            legend=dict(font=dict(color="#6a9ab8", size=9),
                        bgcolor="#060e1e", orientation="h", y=-0.3))
        st.plotly_chart(fd, width='stretch')

    # System health
    with cbr:
        st.markdown("##### System Health")
        health = {
            "Gate Fidelity":     min(99, int(avg_fid)),
            "Quantum Coherence": min(99, int(avg_fid * 0.93)),
            "Error Correction":  (90 if design["err_correct"] == "Surface Code"
                                  else 75 if design["err_correct"] == "Repetition Code" else 50),
            "Thermal Stability": 80 if design["temp_mk"] < 20 else 62,
            "Power Efficiency":  90 if design["low_power"] else (58 if design["hi_perf"] else 78),
            "Clock Accuracy":    98,
        }
        for metric, val in health.items():
            col_ = "#34d399" if val >= 90 else ("#fbbf24" if val >= 70 else "#f87171")
            st.markdown(f"""
            <div style="margin-bottom:.9rem">
              <div style="display:flex;justify-content:space-between;
                          font-size:.85rem;margin-bottom:4px">
                <span style="color:#8eb8d4;font-weight:500">{metric}</span>
                <span style="color:{col_};font-weight:700">{val}%</span>
              </div>
              <div style="background:#0d2040;border-radius:5px;height:7px">
                <div style="background:{col_};width:{val}%;height:7px;
                            border-radius:5px;box-shadow:0 0 6px {col_}55"></div>
              </div>
            </div>""", unsafe_allow_html=True)
