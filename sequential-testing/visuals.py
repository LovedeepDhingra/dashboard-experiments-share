import plotly.graph_objects as go
import math

# ---------------------------------------------------------
# COLOR PALETTE DEFINITION
# ---------------------------------------------------------
# We use distinct colors for TP/FP/TN/FN to create a traffic-light effect.
# Diseased (Truth) is now distinct from FN.
COLORS = {
    # The 4 Confusion Matrix States
    "TP": "#E67E22",       # Orange (Detected Disease)
    "FP": "#FBC02D",       # Yellow (Warning / False Alarm)
    "TN": "#43A047",       # Green (Safe / Correctly Cleared)
    "FN": "#D32F2F",       # Bright Red (Danger / Missed Case) - CHANGED
    
    # The Ground Truth States
    "Diseased": "#8D6E63", # Rust/Brown (Deep Earthy Tone) - CHANGED to be distinct from FN
    "Healthy": "#2E7D32",  # Dark Green 
    
    # Transparent Link Colors for Sankey Flow
    "LinkDiseased": "rgba(141, 110, 99, 0.4)", # Matching Brown
    "LinkHealthy": "rgba(46, 125, 50, 0.4)",   # Matching Green
    "LinkFN": "rgba(211, 47, 47, 0.6)",        # Red for Missed
    "LinkFP": "rgba(251, 192, 45, 0.6)",       # Yellow for False Alarm
    "LinkTP": "rgba(230, 126, 34, 0.6)",       # Orange for Detection
    "LinkTN": "rgba(67, 160, 71, 0.2)"         # Light Green for Safe
}

def create_sankey(results):
    """
    Creates a rigorous Sequential Sankey Diagram.
    
    LOGIC FIX:
    Instead of merging nodes, we keep TP and FP separate at every stage.
    Structure:
    Layer 0: Population
    Layer 1: Truth (Diseased vs Healthy)
    Layer 2 (Test 1): T1_TP, T1_FN, T1_FP, T1_TN
    Layer 3 (Test 2): T2_TP, T2_FN, T2_FP, T2_TN
    ... and so on.
    
    This ensures the color flows remain pure (e.g. Disease stream stays Brown/Orange/Red).
    """
    summary = results['summary']
    history = results['history']
    
    labels = []
    colors = []
    sources = []
    targets = []
    values = []
    link_colors = []
    
    # --- LAYER 0: Total Population ---
    labels.append(f"Total N={summary['Total N']}")
    colors.append("lightgrey")
    idx_pop = 0
    
    # --- LAYER 1: Truth ---
    # We add Diseased first.
    labels.extend(["Diseased (Truth)", "Healthy (Truth)"])
    colors.extend([COLORS["Diseased"], COLORS["Healthy"]])
    idx_dis = 1
    idx_health = 2
    
    # Link Pop -> Truth
    sources.extend([idx_pop, idx_pop])
    targets.extend([idx_dis, idx_health])
    values.extend([summary['Diseased'], summary['Healthy']])
    link_colors.extend([COLORS["LinkDiseased"], COLORS["LinkHealthy"]])
    
    # We track the indices of the "Active" nodes that feed the next test.
    # Initially, these are the Truth nodes.
    prev_tp_idx = idx_dis   # The node holding the sick people
    prev_fp_idx = idx_health # The node holding the healthy people
    
    # --- LAYER 2...N: Tests ---
    for step in history:
        t_name = step['test_name']
        base_idx = len(labels)
        
        # We create 4 explicit nodes for every test to prevent merging logic errors
        # 1. TP Node (Passes to next test)
        # 2. FN Node (Stops here)
        # 3. FP Node (Passes to next test)
        # 4. TN Node (Stops here)
        
        new_labels = [
            f"{t_name} TP", 
            f"{t_name} FN (Miss)", 
            f"{t_name} FP (Alarm)", 
            f"{t_name} TN (Safe)"
        ]
        labels.extend(new_labels)
        
        # Colors for the nodes
        colors.extend([COLORS["TP"], COLORS["FN"], COLORS["FP"], COLORS["TN"]])
        
        # Indices
        idx_tp = base_idx
        idx_fn = base_idx + 1
        idx_fp = base_idx + 2
        idx_tn = base_idx + 3
        
        # --- LINKS FROM PREVIOUS LAYER ---
        
        # 1. Diseased Stream (From prev_tp_idx)
        # Splits into TP (Keep going) and FN (Stop)
        sources.extend([prev_tp_idx, prev_tp_idx])
        targets.extend([idx_tp, idx_fn])
        values.extend([step['TP'], step['FN']])
        link_colors.extend([COLORS["LinkTP"], COLORS["LinkFN"]])
        
        # 2. Healthy Stream (From prev_fp_idx)
        # Splits into FP (Keep going) and TN (Stop)
        sources.extend([prev_fp_idx, prev_fp_idx])
        targets.extend([idx_fp, idx_tn])
        values.extend([step['FP'], step['TN']])
        link_colors.extend([COLORS["LinkFP"], COLORS["LinkTN"]])
        
        # --- UPDATE POINTERS ---
        # The TP and FP nodes of THIS layer become the sources for the NEXT layer
        prev_tp_idx = idx_tp
        prev_fp_idx = idx_fp

    # --- GENERATE FIGURE ---
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors
        )
    )])
    
    fig.update_layout(title_text="Sequential Screening Flow", font_size=12, height=450)
    return fig

def create_waffle_chart(tp, fp, fn, tn, title, total_dots=625):
    """
    Creates a 25x25 Waffle Chart (Dot Matrix) to humanize the data.
    """
    total_people = tp + fp + fn + tn
    if total_people == 0: return go.Figure()

    # Normalize counts to 625 dots
    counts = {
        "TP": int(round(total_dots * (tp / total_people))) if total_people > 0 else 0,
        "FP": int(round(total_dots * (fp / total_people))) if total_people > 0 else 0,
        "FN": int(round(total_dots * (fn / total_people))) if total_people > 0 else 0,
        "TN": int(round(total_dots * (tn / total_people))) if total_people > 0 else 0
    }
    
    # Rounding Error Correction (Dump remainder into TN)
    diff = total_dots - sum(counts.values())
    if diff != 0: counts["TN"] += diff 
        
    rows, cols = 25, 25
    x_vals, y_vals, colors, texts = [], [], [], []
    
    # Fill Order: TP(Orange) -> FN(Red) -> FP(Yellow) -> TN(Green)
    fill_order = ["TP", "FN", "FP", "TN"]
    
    current_idx = 0
    for cat in fill_order:
        count = counts[cat]
        color = COLORS[cat]
        real_count = locals()[cat.lower()]
        pct = (real_count / total_people * 100) if total_people > 0 else 0
        
        for _ in range(count):
            if current_idx >= total_dots: break
            r = current_idx // cols
            c = current_idx % cols
            x_vals.append(c)
            y_vals.append(rows - r - 1) 
            colors.append(color)
            texts.append(f"<b>{cat}</b><br>Count: {real_count}<br>({pct:.1f}%)")
            current_idx += 1
            
    fig = go.Figure(data=go.Scatter(
        x=x_vals, y=y_vals, mode='markers',
        marker=dict(symbol='square', size=12, color=colors, line=dict(width=0.5, color='white')),
        text=texts, hoverinfo='text'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 24.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", range=[-0.5, 24.5]),
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

def create_ground_truth_waffle(diseased, healthy, title, total_dots=625):
    """
    Special Waffle for Ground Truth (2 Categories).
    """
    total = diseased + healthy
    c_dis = int(round(total_dots * (diseased / total)))
    c_health = total_dots - c_dis
    
    x_vals, y_vals, colors, texts = [], [], [], []
    
    # Fill Diseased (Brown) then Healthy (Green)
    count_map = [
        ("Diseased", c_dis, COLORS["Diseased"], diseased),
        ("Healthy", c_health, COLORS["Healthy"], healthy)
    ]
    
    idx, rows, cols = 0, 25, 25
    for label, count, color, real_val in count_map:
        for _ in range(count):
            if idx >= total_dots: break
            r = idx // cols
            c = idx % cols
            x_vals.append(c)
            y_vals.append(rows - r - 1)
            colors.append(color)
            texts.append(f"{label}: {real_val}")
            idx += 1
            
    fig = go.Figure(data=go.Scatter(
        x=x_vals, y=y_vals, mode='markers',
        marker=dict(symbol='square', size=12, color=colors, line=dict(width=0.5, color='white')),
        text=texts, hoverinfo='text'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 24.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", range=[-0.5, 24.5]),
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig