import plotly.graph_objects as go
import math

# ---------------------------------------------------------
# COLOR PALETTE DEFINITION
# ---------------------------------------------------------
# We use distinct colors for TP/FP/TN/FN to create a traffic-light effect.
COLORS = {
    "TP": "#6495ED",       # Blue (Detected Disease)
    "FP": "#FBC02D",       # Yellow (Warning / False Alarm)
    "TN": "#43A047",       # Green (Safe / Correctly Cleared)
    "FN": "#D32F2F",       # Bright Red (Danger / Missed Case)
    
    "Diseased": "#8D6E63", # Rust/Brown (Deep Earthy Tone)
    "Healthy": "#2E7D32",  # Dark Green 
    
    # Transparent Link Colors for Sankey Flow
    "LinkDiseased": "rgba(141, 110, 99, 0.4)", # Matching Brown
    "LinkHealthy": "rgba(46, 125, 50, 0.4)",   # Matching Green
    "LinkFN": "rgba(211, 47, 47, 0.6)",        # Red for Missed
    "LinkFP": "rgba(251, 192, 45, 0.6)",       # Yellow for False Alarm
    "LinkTP": "rgba(41, 128, 185, 0.3)",       # Blue for Detection
    "LinkTN": "rgba(67, 160, 71, 0.2)"         # Light Green for Safe
}

def create_sankey(results):
    """
    Creates a rigorous Sequential Sankey Diagram.
    
    LOGIC UPDATE:
    - Dynamic Ordering: The code checks if Diseased or Healthy is the smaller population.
    - The smaller population is added to the node list FIRST. 
    - This hints the Plotly layout engine to render it at the top of the chart.
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
    
    # --- LAYER 1: Truth (Dynamic Sorting) ---
    
    # Determine which group is smaller to place it 'on top' (first in list)
    num_d = summary['Diseased']
    num_h = summary['Healthy']
    
    # We define the order we want to add them. 
    # Tuple structure: (Name, Count, Color, LinkColor, TypeKey)
    d_data = ("Diseased", num_d, COLORS["Diseased"], COLORS["LinkDiseased"], "D")
    h_data = ("Healthy", num_h, COLORS["Healthy"], COLORS["LinkHealthy"], "H")
    
    # If Diseased is smaller (or equal), it goes first. Otherwise Healthy goes first.
    if num_d <= num_h:
        layer1_order = [d_data, h_data]
    else:
        layer1_order = [h_data, d_data]
        
    # Variables to store the indices for the next step
    # We need to know where 'Diseased' and 'Healthy' ended up in the node list
    prev_indices = {} 
    
    for item in layer1_order:
        name, count, color, link_col, type_key = item
        
        # Add Node
        current_idx = len(labels)
        labels.append(name)
        colors.append(color)
        
        # Add Link from Pop -> This Node
        sources.append(idx_pop)
        targets.append(current_idx)
        values.append(count)
        link_colors.append(link_col)
        
        # Store index for the next layer's logic
        prev_indices[type_key] = current_idx

    # Set pointers for the next loop
    prev_tp_idx = prev_indices["D"]  # The node holding the sick people
    prev_fp_idx = prev_indices["H"]  # The node holding the healthy people
    
    # --- LAYER 2...N: Tests ---
    for step in history:
        t_name = step['test_name']
        base_idx = len(labels)
        
        # Create 4 explicit nodes for every test layer
        # Order: TP, FN, FP, TN
        new_labels = [
            f"{t_name} TP", 
            f"{t_name} FN", 
            f"{t_name} FP", 
            f"{t_name} TN"
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
        
        # 1. Diseased Stream (From prev_tp_idx) -> TP & FN
        sources.extend([prev_tp_idx, prev_tp_idx])
        targets.extend([idx_tp, idx_fn])
        values.extend([step['TP'], step['FN']])
        link_colors.extend([COLORS["LinkTP"], COLORS["LinkFN"]])
        
        # 2. Healthy Stream (From prev_fp_idx) -> FP & TN
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
        # Text styling: Black for readability in light mode
        textfont=dict(color="black", size=12),
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
    
    fig.update_layout(title_text="Sequential Screening Flow", font_size=14, height=450)
    return fig

def create_waffle_chart(tp, fp, fn, tn, title, total_dots=625):
    """
    Creates a 25x25 Waffle Chart (Dot Matrix) to humanize the data.
    Uses a fixed grid size (625 dots) so visuals are comparable across different N.
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
    
    # Fill Order: TP(Blue) -> FN(Red) -> FP(Yellow) -> TN(Green)
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
    Special Waffle for Ground Truth (2 Categories: Diseased vs Healthy).
    """
    total = diseased + healthy
    if total == 0: return go.Figure()
    
    # Normalized counts
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
        pct = (real_val / total * 100) if total > 0 else 0
        for _ in range(count):
            if idx >= total_dots: break
            r = idx // cols
            c = idx % cols
            x_vals.append(c)
            y_vals.append(rows - r - 1)
            colors.append(color)
            texts.append(f"<b>{label}</b><br>Count: {real_val}<br>({pct:.1f}%)")
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