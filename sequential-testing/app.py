import streamlit as st
import calculations
import visuals

# ==========================================
# PAGE CONFIGURATION
# ==========================================
# The theme is now controlled by .streamlit/config.toml
st.set_page_config(layout="wide", page_title="Sequential Screening Simulator")

# --- CSS STYLING ---
st.markdown("""
<style>
    /* Card Styling */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-val { font-size: 20px; font-weight: 700; color: #2c3e50; }
    .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
    
    /* Cleaner Button Styling */
    /* Icons are added directly in the button text, styling handles layout */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3em;
        border: none;
        background-color: #f0f2f6;
        color: #31333F;
        transition: all 0.2s;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #e1e4e8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: SYNCED INPUTS ---
def synced_input(label, key_prefix, min_val, max_val, default_val, step=0.1):
    """
    Creates a bidirectional Slider + NumberInput with better alignment.
    """
    # Use vertical_alignment="bottom" to align the slider and text box
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom") 
    
    slider_key = f"{key_prefix}_slider"
    num_key = f"{key_prefix}_num"
    
    if slider_key not in st.session_state: st.session_state[slider_key] = default_val
    if num_key not in st.session_state: st.session_state[num_key] = default_val
        
    def update_from_slider(): st.session_state[num_key] = st.session_state[slider_key]
    def update_from_num():
        val = max(min_val, min(max_val, st.session_state[num_key]))
        st.session_state[slider_key] = val
        
    with col1: 
        st.slider(label, min_val, max_val, step=step, key=slider_key, on_change=update_from_slider)
    with col2: 
        st.number_input(label, min_val, max_val, step=step, key=num_key, on_change=update_from_num, label_visibility="hidden")
        
    return st.session_state[slider_key]

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("Configuration")

    # 1. Population Inputs
    st.header("Population Settings")
    # Default N updated to 1000
    N = st.number_input("Total Population (N)", value=1000, step=100)
    # Default Prevalence updated to 12.9%
    prev = synced_input("Prevalence (%)", "prev", 0.0, 100.0, 12.9)

    st.divider()

    # 2. Test Inputs
    st.header("Screening Tests")

    # Initialize with 2 tests by default
    if 'num_tests' not in st.session_state: st.session_state['num_tests'] = 2

    def add_test(): st.session_state['num_tests'] += 1
    def remove_test(): 
        if st.session_state['num_tests'] > 1: st.session_state['num_tests'] -= 1

    # Define default values for the first two tests
    default_tests = [
        {"name": "AI-ECG", "sens": 90.4, "spec": 58.7},
        {"name": "AI-POCUS", "sens": 96.0, "spec": 96.0}
    ]

    tests_config = []
    for i in range(st.session_state['num_tests']):
        st.subheader(f"Test {i+1}")
        
        # Get defaults if available, else use generic ones
        if i < len(default_tests):
            d_name = default_tests[i]["name"]
            d_sens = default_tests[i]["sens"]
            d_spec = default_tests[i]["spec"]
        else:
            d_name = f"Test {i+1}"
            d_sens = 90.0
            d_spec = 80.0
            
        t_name = st.text_input(f"Test Name", value=d_name, key=f"name_{i}")
        sens = synced_input(f"Sensitivity", f"sens_{i}", 0.0, 100.0, d_sens)
        spec = synced_input(f"Specificity", f"spec_{i}", 0.0, 100.0, d_spec)
        
        tests_config.append({"name": t_name, "sensitivity": sens, "specificity": spec})
        st.markdown("---")

    # Cleaner Action Buttons with Icons First
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.button("➕ Add Test", on_click=add_test, use_container_width=True)
    with b_col2:
        disabled_status = st.session_state['num_tests'] <= 1
        st.button("➖ Remove Test", on_click=remove_test, disabled=disabled_status, use_container_width=True)

# ==========================================
# MAIN DASHBOARD RENDERING
# ==========================================
results = calculations.run_simulation(N, prev, tests_config)
summary = results['summary']

st.title("Sequential Screening Dashboard")

# ROW 1: Sankey Flow
st.subheader("1. Patient Flow")
st.caption("Visualizes how the population is filtered through sequential tests.")
sankey_fig = visuals.create_sankey(results)
st.plotly_chart(sankey_fig, use_container_width=True)

# ROW 2: Global Metrics
st.subheader("2. Overall Performance Metrics")
def metric_card(col, label, val):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-val">{val}</div>
    </div>
    """, unsafe_allow_html=True)

# Reordered Metrics as requested:
# Row 1: Sens, Spec, Screen Pos Rate, Screen Neg Rate
r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
metric_card(r2_col1, "Global Sensitivity", f"{summary['Global Sens']:.1f}%")
metric_card(r2_col2, "Global Specificity", f"{summary['Global Spec']:.1f}%")
metric_card(r2_col3, "Screen Positivity Rate", f"{summary['Screen Pos Rate']:.1f}%")
metric_card(r2_col4, "Screen Negativity Rate", f"{summary['Screen Neg Rate']:.1f}%")

# Row 2: PPV, NPV, LR+, LR-
r3_col1, r3_col2, r3_col3, r3_col4 = st.columns(4)
metric_card(r3_col1, "Global PPV", f"{summary['Global PPV']:.1f}%")
metric_card(r3_col2, "Global NPV", f"{summary['Global NPV']:.1f}%")
metric_card(r3_col3, "Positive LR (LR+)", f"{summary['Global LR+']:.1f}")
metric_card(r3_col4, "Negative LR (LR-)", f"{summary['Global LR-']:.2f}")

st.markdown("---")

# ROW 3: Population Comparison
st.subheader("3. Population Comparison")
row3_left, row3_right = st.columns(2)

with row3_left:
    st.markdown("### Disease Prevalence")
    st.markdown(f"""
    **Total N:** {summary['Total N']}
    * <span style='color:#8D6E63'>**Diseased:** {summary['Diseased']}</span>
    * <span style='color:#2E7D32'>**Healthy:** {summary['Healthy']}</span>
    """, unsafe_allow_html=True)
    fig_truth = visuals.create_ground_truth_waffle(
        summary['Diseased'], summary['Healthy'], 
        title="Ground Truth Breakdown"
    )
    st.plotly_chart(fig_truth, use_container_width=True)

with row3_right:
    st.markdown("### Screening Approach Results")
    st.markdown(f"""
    **Final Classification:**
    * <span style='color:#E67E22'>**TP:** {summary['Final TP']}</span> | <span style='color:#D32F2F'>**FN:** {summary['Final FN']}</span>
    * <span style='color:#FBC02D'>**FP:** {summary['Final FP']}</span> | <span style='color:#43A047'>**TN:** {summary['Final TN']}</span>
    """, unsafe_allow_html=True)
    fig_final = visuals.create_waffle_chart(
        summary['Final TP'], summary['Final FP'], 
        summary['Final FN'], summary['Final TN'],
        title="Final Screening Outcome"
    )
    st.plotly_chart(fig_final, use_container_width=True)

st.markdown("---")

# ROW 4+: Individual Steps
st.subheader("4. Step-by-Step Test Performance")
for step in results['history']:
    st.markdown(f"### {step['test_name']}")
    c_left, c_right = st.columns([1, 2])
    
    # Calculate step-specific PPV/NPV for display
    total_pos = step['TP'] + step['FP']
    total_neg = step['TN'] + step['FN']
    step_ppv = (step['TP'] / total_pos * 100) if total_pos > 0 else 0
    step_npv = (step['TN'] / total_neg * 100) if total_neg > 0 else 0
    
    with c_left:
        # Comprehensive Metric Display
        st.markdown(f"""
        **Input N:** {step['input_n']}
        
        **Counts:**
        - <span style='color:#E67E22'><b>TP:</b> {step['TP']}</span> | <span style='color:#D32F2F'><b>FN:</b> {step['FN']}</span>
        - <span style='color:#FBC02D'><b>FP:</b> {step['FP']}</span> | <span style='color:#43A047'><b>TN:</b> {step['TN']}</span>
        
        **Metrics:**
        - **Sensitivity:** {step['sens']:.1f}% | **Specificity:** {step['spec']:.1f}%
        - **Screen Positivity Rate:** {step['pos_rate']*100:.1f}% | **Screen Negativity Rate:** {step['neg_rate']*100:.1f}%
        - **PPV:** {step_ppv:.1f}% | **NPV:** {step_npv:.1f}%
        - **LR+:** {step['lr_plus']:.1f} | **LR-:** {step['lr_minus']:.2f}
        """, unsafe_allow_html=True)
        
    with c_right:
        fig_step = visuals.create_waffle_chart(
            step['TP'], step['FP'], step['FN'], step['TN'],
            title=f"Results: {step['test_name']}"
        )
        st.plotly_chart(fig_step, use_container_width=True)
    st.divider()