import math
import numpy as np
import plotly.graph_objects as go


# ═══════════════════════════════════════════════════════════════════════════════
# TOPOLOGY GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_topology(n):
    """Returns qubit positions and coupler edges for a given qubit count."""
    qubits = {}
    couplers = []
    spacing = 1.8

    if n <= 4:
        for i in range(n):
            qubits[i] = (i * spacing - (n - 1) * spacing / 2, 0)
        for i in range(n - 1):
            couplers.append((i, i + 1))
    elif n == 5:
        qubits[0] = (0, 0)
        qubits[1] = (0, spacing)
        qubits[2] = (spacing, 0)
        qubits[3] = (0, -spacing)
        qubits[4] = (-spacing, 0)
        couplers = [(0, 1), (0, 2), (0, 3), (0, 4)]
    elif n <= 8:
        cols = math.ceil(n / 2)
        for i in range(n):
            r, c = divmod(i, cols)
            qubits[i] = (c * spacing - (cols - 1) * spacing / 2, (0.5 - r) * spacing)
        for r in range(2):
            for c in range(cols - 1):
                i1, i2 = r * cols + c, r * cols + c + 1
                if i1 < n and i2 < n:
                    couplers.append((i1, i2))
        for c in range(cols):
            i1, i2 = c, cols + c
            if i1 < n and i2 < n:
                couplers.append((i1, i2))
    else:
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        for i in range(n):
            r, c = divmod(i, cols)
            qubits[i] = (
                c * spacing - (cols - 1) * spacing / 2,
                (rows - 1) * spacing / 2 - r * spacing,
            )
        for r in range(rows):
            for c in range(cols - 1):
                i1, i2 = r * cols + c, r * cols + c + 1
                if i1 < n and i2 < n:
                    couplers.append((i1, i2))
        for r in range(rows - 1):
            for c in range(cols):
                i1, i2 = r * cols + c, (r + 1) * cols + c
                if i1 < n and i2 < n:
                    couplers.append((i1, i2))
    return qubits, couplers


# ═══════════════════════════════════════════════════════════════════════════════
# PATH GEOMETRY UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _fillet_path(pts, r=0.18, n_arc=10):
    """Round corners of a polyline with circular arcs."""
    if len(pts) < 3:
        return list(pts)
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = np.array(pts[i - 1]), np.array(pts[i]), np.array(pts[i + 1])
        v0, v2 = p0 - p1, p2 - p1
        l0, l2 = np.linalg.norm(v0), np.linalg.norm(v2)
        if l0 < 1e-9 or l2 < 1e-9:
            continue
        u0, u2 = v0 / l0, v2 / l2
        ra = min(r, l0 * 0.45, l2 * 0.45)
        dot = float(np.clip(np.dot(u0, u2), -1, 1))
        ang = math.acos(dot)
        if ang < 0.02 or math.pi - ang < 0.02:
            out.append(tuple(p1))
            continue
        t0, t2 = p1 + u0 * ra, p1 + u2 * ra
        b = u0 + u2
        bl = np.linalg.norm(b)
        if bl > 1e-9:
            b /= bl
        cen = p1 + b * math.sqrt(ra ** 2 + (ra / math.tan(ang / 2)) ** 2)
        a0 = math.atan2((t0 - cen)[1], (t0 - cen)[0])
        a2 = math.atan2((t2 - cen)[1], (t2 - cen)[0])
        da = (a2 - a0) % (2 * math.pi)
        if da > math.pi:
            da -= 2 * math.pi
        for j in range(n_arc + 1):
            a = a0 + j * da / n_arc
            out.append((float(cen[0] + math.cos(a) * ra), float(cen[1] + math.sin(a) * ra)))
    out.append(pts[-1])
    return out


def _buffer_path(pts, half_w):
    """Expand a polyline into a filled polygon of given half-width."""
    if len(pts) < 2:
        return [], []
    arr = np.array(pts, dtype=float)
    left, right = [], []
    for i in range(len(arr)):
        if i == 0:
            d = arr[1] - arr[0]
        elif i == len(arr) - 1:
            d = arr[-1] - arr[-2]
        else:
            d = arr[i + 1] - arr[i - 1]
        ln = np.linalg.norm(d)
        if ln < 1e-9:
            continue
        d /= ln
        n = np.array([-d[1], d[0]])
        left.append(arr[i] + n * half_w)
        right.append(arr[i] - n * half_w)
    if not left:
        return [], []
    poly = left + right[::-1] + [left[0]]
    xs = [float(p[0]) for p in poly]
    ys = [float(p[1]) for p in poly]
    return xs, ys


# ═══════════════════════════════════════════════════════════════════════════════
# LITHOGRAPHY COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

_PALETTE = {
    "substrate":    "#050a12",
    "ground":       "#1e2a38",
    "metal":        "#a8c4d8",
    "metal_bright": "#d0e4f0",
    "gap":          "#050a12",
    "junction":     "#e8c060",
    "label":        "#607890",
    "bg":           "#020406",
}

# CPW widths in data-coordinate units
_W_GAP   = 0.14       # full etch width
_W_TRACE = 0.045      # center conductor
_W_FEED_GAP   = 0.22  # feedline etch width
_W_FEED_TRACE = 0.08  # feedline conductor


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FABRICATED-CHIP RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def draw_superconducting_chip(design: dict) -> go.Figure:
    n = design["n_qubits"]
    P = _PALETTE
    qubits, couplers = generate_topology(n)

    # --- die boundaries ---
    xs = [x for x, y in qubits.values()]
    ys = [y for x, y in qubits.values()]
    qx0, qx1 = (min(xs), max(xs)) if xs else (0, 0)
    qy0, qy1 = (min(ys), max(ys)) if ys else (0, 0)

    pad = 1.8
    ctrl_margin = 1.6
    bus_margin = 2.2
    die_x0, die_x1 = qx0 - pad, qx1 + pad
    die_y0, die_y1 = qy0 - ctrl_margin - 0.6, qy1 + bus_margin + 0.4

    fig = go.Figure()

    # outer vacuum
    fig.add_shape(type="rect",
        x0=die_x0 - 1.5, x1=die_x1 + 1.5, y0=die_y0 - 1.5, y1=die_y1 + 1.5,
        fillcolor=P["bg"], line_color=P["bg"], layer="below")

    # ground plane
    fig.add_shape(type="rect",
        x0=die_x0, x1=die_x1, y0=die_y0, y1=die_y1,
        fillcolor=P["ground"],
        line=dict(color=P["metal"], width=1.5),
        layer="below")

    # ------------------------------------------------------------------
    # drawing helpers (closures over fig and palette)
    # ------------------------------------------------------------------

    def _cpw(pts, w_gap=_W_GAP, w_trace=_W_TRACE, hover_label=None):
        """Draw a CPW trace: etched gap polygon + center conductor polygon."""
        pts = _fillet_path(pts, r=0.2)
        gx, gy = _buffer_path(pts, w_gap / 2)
        if gx:
            fig.add_trace(go.Scatter(x=gx, y=gy, fill="toself",
                fillcolor=P["gap"], line=dict(color=P["gap"], width=0),
                mode="lines", hoverinfo="none", showlegend=False))
        tx, ty = _buffer_path(pts, w_trace / 2)
        if tx:
            ht = "text" if hover_label else "none"
            fig.add_trace(go.Scatter(x=tx, y=ty, fill="toself",
                fillcolor=P["metal"], line=dict(color=P["metal"], width=0),
                mode="lines", hoverinfo=ht,
                hovertext=hover_label,
                showlegend=False))

    def _xmon(cx, cy, qid):
        """XMON transmon: cross-shaped etch with metal island and junction."""
        el, ew = 0.55, 0.22   # etch arm half-length, half-width
        ml, mw = 0.42, 0.12   # metal arm half-length, half-width

        # etch pocket (two crossed rectangles)
        for dx, dy, hw, hl in [
            (0, 0, el, ew),  # horizontal bar
            (0, 0, ew, el),  # vertical bar
        ]:
            fig.add_shape(type="rect",
                x0=cx - hw, x1=cx + hw, y0=cy - hl, y1=cy + hl,
                fillcolor=P["gap"], line_color=P["gap"])

        # metal island
        for hw, hl in [(ml, mw), (mw, ml)]:
            fig.add_shape(type="rect",
                x0=cx - hw, x1=cx + hw, y0=cy - hl, y1=cy + hl,
                fillcolor=P["metal_bright"], line_color=P["metal_bright"])

        # Josephson junction at bottom arm
        jw = 0.015
        fig.add_shape(type="rect",
            x0=cx - jw * 2, x1=cx + jw * 2,
            y0=cy - el, y1=cy - ml,
            fillcolor=P["gap"], line_color=P["gap"])
        for sign in (-1, 1):
            fig.add_shape(type="line",
                x0=cx + sign * jw, y0=cy - el,
                x1=cx + sign * jw, y1=cy - ml,
                line=dict(color=P["junction"], width=1.5))
        # small JJ cross
        fig.add_shape(type="line",
            x0=cx - jw, y0=cy - (el + ml) / 2,
            x1=cx + jw, y1=cy - (el + ml) / 2,
            line=dict(color=P["junction"], width=1))

        # hover target (invisible scatter point)
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy], mode="markers",
            marker=dict(size=18, color="rgba(0,0,0,0)"),
            hoverinfo="text",
            hovertext=f"<b>Q{qid}</b><br>Type: XMON Transmon<br>f_r ≈ {5.0 + qid * 0.12:.2f} GHz",
            showlegend=False))

        # label
        fig.add_annotation(x=cx, y=cy + el + 0.12, text=f"Q{qid}",
            showarrow=False,
            font=dict(size=9, color=P["label"], family="monospace"))

    def _idc_coupler(x0, y0, x1, y1, cid):
        """Interdigitated capacitive coupler between two qubits."""
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        horiz = abs(x1 - x0) > abs(y1 - y0)
        cw = 0.32 if horiz else 0.18
        ch = 0.18 if horiz else 0.32

        # etch window
        fig.add_shape(type="rect",
            x0=cx - cw / 2, x1=cx + cw / 2, y0=cy - ch / 2, y1=cy + ch / 2,
            fillcolor=P["gap"], line_color=P["gap"])

        # interdigitated fingers
        nf = 5
        if horiz:
            for i in range(nf):
                fy = cy - ch / 2 + (i + 0.5) * ch / nf
                from_left = (i % 2 == 0)
                fx0 = cx - cw / 2 + (0.04 if from_left else 0.0)
                fx1 = cx + cw / 2 - (0.0 if from_left else 0.04)
                fig.add_shape(type="rect",
                    x0=fx0, x1=fx1, y0=fy - 0.012, y1=fy + 0.012,
                    fillcolor=P["metal"], line_color=P["metal"])
        else:
            for i in range(nf):
                fx = cx - cw / 2 + (i + 0.5) * cw / nf
                from_bot = (i % 2 == 0)
                fy0 = cy - ch / 2 + (0.04 if from_bot else 0.0)
                fy1 = cy + ch / 2 - (0.0 if from_bot else 0.04)
                fig.add_shape(type="rect",
                    x0=fx - 0.012, x1=fx + 0.012, y0=fy0, y1=fy1,
                    fillcolor=P["metal"], line_color=P["metal"])

        # CPW leads into coupler
        arm = 0.55  # XMON arm half-length
        if horiz:
            _cpw([(x0 + arm, y0), (cx - cw / 2, cy)])
            _cpw([(cx + cw / 2, cy), (x1 - arm, y1)])
        else:
            _cpw([(x0, y0 - arm), (cx, cy + ch / 2)])
            _cpw([(cx, cy - ch / 2), (x1, y1 + arm)])

        # hover
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy], mode="markers",
            marker=dict(size=12, color="rgba(0,0,0,0)"),
            hoverinfo="text",
            hovertext=f"<b>Coupler C{cid}</b><br>Type: IDC<br>Q{x0}↔Q{y0}",
            showlegend=False))

    def _resonator(qid, qx, qy, bus_y):
        """λ/4 readout resonator meandering from qubit to bus."""
        arm = 0.55
        start_y = qy + arm + 0.06  # just above XMON top arm

        # frequency-aware length variation
        base_loops = 3
        extra = (qid * 7 + 3) % 5   # pseudo-random but deterministic
        loops = base_loops + extra
        amp = 0.18 + (qid % 3) * 0.04  # slight amplitude variation

        pts = [(qx, start_y)]
        cy = start_y + 0.08
        pts.append((qx, cy))

        avail = bus_y - cy - 0.3
        step = avail / max(loops * 2, 1)

        cx = qx
        for _ in range(loops):
            cx -= amp
            pts.append((cx, cy))
            cy += step
            pts.append((cx, cy))
            cx += 2 * amp
            pts.append((cx, cy))
            cy += step
            pts.append((cx, cy))
            cx -= amp
            pts.append((cx, cy))

        pts.append((qx, bus_y))
        _cpw(pts, hover_label=f"Resonator R{qid}<br>f_r ≈ {6.8 + qid * 0.15:.2f} GHz")

    def _control_line(qid, qx, qy):
        """XY/Z control line from qubit bottom arm to die edge."""
        arm = 0.55
        pts = [(qx, qy - arm - 0.06), (qx, die_y0 + 0.3)]
        _cpw(pts, hover_label=f"Control XY{qid}")
        _launch_pad(qx, die_y0 + 0.3, "v", -1)

    def _launch_pad(bx, by, orient="h", d=1):
        """Tapered wirebond launch pad."""
        s = 0.35
        if orient == "h":
            ex = [bx, bx + d * s * 0.6, bx + d * s * 2.2, bx + d * s * 2.2, bx + d * s * 0.6, bx]
            ey = [by - 0.06, by - s * 0.55, by - s * 0.55, by + s * 0.55, by + s * 0.55, by + 0.06]
            mx = [bx, bx + d * s * 0.5, bx + d * s * 2.1, bx + d * s * 2.1, bx + d * s * 0.5, bx]
            my = [by, by - s * 0.4, by - s * 0.4, by + s * 0.4, by + s * 0.4, by]
        else:
            ex = [bx - 0.06, bx - s * 0.55, bx - s * 0.55, bx + s * 0.55, bx + s * 0.55, bx + 0.06]
            ey = [by, by + d * s * 0.6, by + d * s * 2.2, by + d * s * 2.2, by + d * s * 0.6, by]
            mx = [bx, bx - s * 0.4, bx - s * 0.4, bx + s * 0.4, bx + s * 0.4, bx]
            my = [by, by + d * s * 0.5, by + d * s * 2.1, by + d * s * 2.1, by + d * s * 0.5, by]
        fig.add_trace(go.Scatter(x=ex, y=ey, fill="toself",
            fillcolor=P["gap"], line=dict(color=P["gap"], width=0),
            mode="lines", hoverinfo="none", showlegend=False))
        fig.add_trace(go.Scatter(x=mx, y=my, fill="toself",
            fillcolor=P["metal_bright"], line=dict(color=P["metal_bright"], width=0),
            mode="lines", hoverinfo="none", showlegend=False))

    def _alignment_mark(cx, cy):
        s = 0.18
        fig.add_shape(type="rect",
            x0=cx - s, x1=cx + s, y0=cy - s, y1=cy + s,
            fillcolor=P["gap"], line_color=P["gap"])
        fig.add_shape(type="rect",
            x0=cx - s * 0.7, x1=cx + s * 0.7, y0=cy - 0.01, y1=cy + 0.01,
            fillcolor=P["metal"], line_color=P["metal"])
        fig.add_shape(type="rect",
            x0=cx - 0.01, x1=cx + 0.01, y0=cy - s * 0.7, y1=cy + s * 0.7,
            fillcolor=P["metal"], line_color=P["metal"])

    # ------------------------------------------------------------------
    # RENDER PIPELINE
    # ------------------------------------------------------------------

    # 1) Qubits
    for qid, (qx, qy) in qubits.items():
        _xmon(qx, qy, qid)

    # 2) Control lines
    for qid, (qx, qy) in qubits.items():
        _control_line(qid, qx, qy)

    # 3) Couplers
    for ci, (q1, q2) in enumerate(couplers):
        _idc_coupler(qubits[q1][0], qubits[q1][1],
                     qubits[q2][0], qubits[q2][1], ci)

    # 4) Readout bus + resonators
    bus_y = qy1 + bus_margin - 0.2

    if n <= 6:
        # direct ports
        left_ids = list(qubits.keys())[:math.ceil(n / 2)]
        for qid, (qx, qy) in qubits.items():
            _resonator(qid, qx, qy, bus_y)
            if qid in left_ids:
                tx = die_x0 + 0.3
                _cpw([(qx, bus_y), (tx, bus_y)],
                     hover_label=f"Readout port R{qid}")
                _launch_pad(tx, bus_y, "h", -1)
            else:
                tx = die_x1 - 0.3
                _cpw([(qx, bus_y), (tx, bus_y)],
                     hover_label=f"Readout port R{qid}")
                _launch_pad(tx, bus_y, "h", 1)
    else:
        # shared multiplexed feedline
        _cpw([(die_x0 + 0.3, bus_y), (die_x1 - 0.3, bus_y)],
             w_gap=_W_FEED_GAP, w_trace=_W_FEED_TRACE,
             hover_label="Readout feedline bus")
        _launch_pad(die_x0 + 0.3, bus_y, "h", -1)
        _launch_pad(die_x1 - 0.3, bus_y, "h", 1)

        for qid, (qx, qy) in qubits.items():
            _resonator(qid, qx, qy, bus_y - 0.15)
            # coupling spur
            _cpw([(qx - 0.15, bus_y - 0.15), (qx + 0.15, bus_y - 0.15)])

    # 5) Alignment marks
    am = 0.5
    for ax, ay in [
        (die_x0 + am, die_y0 + am), (die_x1 - am, die_y0 + am),
        (die_x0 + am, die_y1 - am), (die_x1 - am, die_y1 - am),
    ]:
        _alignment_mark(ax, ay)

    # 6) Die label
    fig.add_annotation(
        x=die_x1 - 0.4, y=die_y0 + 0.35,
        text=f"{n}Q · {design.get('qubits_type', 'Processor')}",
        showarrow=False, xanchor="right",
        font=dict(size=11, color=P["label"], family="monospace"))

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    vp_pad = 0.8
    fig.update_layout(
        height=750,
        plot_bgcolor=P["bg"],
        paper_bgcolor=P["bg"],
        xaxis=dict(
            showticklabels=False, showgrid=False, zeroline=False,
            range=[die_x0 - vp_pad, die_x1 + vp_pad],
            scaleanchor="y", scaleratio=1,
            fixedrange=False,
        ),
        yaxis=dict(
            showticklabels=False, showgrid=False, zeroline=False,
            range=[die_y0 - vp_pad, die_y1 + vp_pad],
            fixedrange=False,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        dragmode="pan",
        hoverlabel=dict(
            bgcolor="#0d1b2e",
            bordercolor="#38a0c8",
            font=dict(color="#d0e4f0", size=12, family="monospace"),
        ),
    )
    fig.update_layout(modebar=dict(
        bgcolor="rgba(0,0,0,0)",
        color="#4a7a9b",
        activecolor="#38a0c8",
        orientation="v",
    ))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMATIC VIEW RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def draw_schematic_chip(design: dict) -> go.Figure:
    """Clean schematic view with topology graph."""
    n = design["n_qubits"]
    BG   = "#f0f4f8"
    SUB  = "#e2e8f0"
    LINE = "#2d3748"
    BOX  = "#cbd5e0"
    AXS  = "#a0aec0"

    qubits, couplers = generate_topology(n)

    xs = [x for x, y in qubits.values()]
    ys = [y for x, y in qubits.values()]
    x0, x1 = (min(xs) - 2, max(xs) + 2) if xs else (-2, 2)
    y0, y1 = (min(ys) - 2, max(ys) + 2) if ys else (-2, 2)

    fig = go.Figure()
    fig.add_shape(type="rect", x0=x0 - 1, x1=x1 + 1, y0=y0 - 1, y1=y1 + 1,
                  fillcolor=BG, line_color=BG, layer="below")
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                  fillcolor=SUB, line=dict(color=AXS, width=1), layer="below")

    for q1, q2 in couplers:
        cx1, cy1 = qubits[q1]
        cx2, cy2 = qubits[q2]
        fig.add_trace(go.Scatter(x=[cx1, cx2], y=[cy1, cy2], mode="lines",
            line=dict(color=LINE, width=2, dash="dot"),
            hoverinfo="none", showlegend=False))

    for qid, (qx, qy) in qubits.items():
        w, h = 0.6, 0.45
        fig.add_shape(type="rect",
            x0=qx - w / 2, x1=qx + w / 2, y0=qy - h / 2, y1=qy + h / 2,
            fillcolor=BOX, line=dict(color=LINE, width=1.5))
        fig.add_annotation(x=qx, y=qy, text=f"Q{qid}", showarrow=False,
            font=dict(size=10, color=LINE, family="monospace"))

    fig.update_layout(
        height=500,
        plot_bgcolor=BG, paper_bgcolor=BG,
        xaxis=dict(showticklabels=True, showgrid=True, zeroline=True,
                   range=[x0 - 1, x1 + 1], scaleanchor="y", scaleratio=1,
                   gridcolor="#d1dce8", tickcolor=AXS, tickfont=dict(color=AXS)),
        yaxis=dict(showticklabels=True, showgrid=True, zeroline=True,
                   range=[y0 - 1, y1 + 1],
                   gridcolor="#d1dce8", tickcolor=AXS, tickfont=dict(color=AXS)),
        margin=dict(l=30, r=10, t=10, b=30),
        showlegend=False,
    )
    return fig
