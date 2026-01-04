import streamlit as st
import calculations
import visuals

# ==========================================
# PAGE CONFIGURATION
# ==========================================
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
    
    /* Button Styling - Making them full width and cleaner */
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER: SYNCED INPUTS ---
def synced_input(label, key_prefix, min_val, max_val, default_val, step=0.1):
    """
    Creates a bidirectional Slider + NumberInput.
    
    CRITICAL LAYOUT NOTE:
    This function uses st.columns(). For this to render in the sidebar,
    it MUST be called inside a 'with st.sidebar:' block in the main code.
    """
    # Create columns. If called inside 'with st.sidebar:', these will be sidebar columns.
    col1, col2 = st.columns([2, 1]) 
    
    slider_key = f"{key_prefix}_slider"
    num_key = f"{key_prefix}_num"
    
    # Initialize Session State
    if slider_key not in st.session_state: st.session_state[slider_key] = default_val
    if num_key not in st.session_state: st.session_state[num_key] = default_val
        
    # Callbacks to sync the two widgets
    def update_from_slider(): st.session_state[num_key] = st.session_state[slider_key]
    def update_from_num():
        val = max(min_val, min(max_val, st.session_state[num_key]))
        st.session_state[slider_key] = val
        
    # Render Widgets
    with col1: 
        st.slider(label, min_val, max_val, step=step, key=slider_key, on_change=update_from_slider)
    with col2: 
        # Number input with hidden label to align with slider
        st.number_input(label, min_val, max_val, step=step, key=num_key, on_change=update_from_num, label_visibility="hidden")
        
    return st.session_state[slider_key]

# ==========================================
# SIDEBAR CONFIGURATION (STRICT CONTEXT)
# ==========================================
# We use 'with st.sidebar:' to ensure ALL columns and widgets stay on the left.

with st.sidebar:
    st.title("Configuration")

    # 1. Population Inputs
    # --------------------
    st.header("Population Settings")
    N = st.number_input("Total Population (N)", value=1000, step=100)
    
    # Prevalence Input
    # This will now correctly render in the sidebar because of the 'with st.sidebar' context.
    prev = synced_input("Prevalence (%)", "prev", 0.0, 100.0, 10.0)

    st.divider()

    # 2. Test Inputs
    # --------------
    st.header("Screening Tests")

    # Initialize test count
    if 'num_tests' not in st.session_state: st.session_state['num_tests'] = 1

    # Callbacks for Buttons
    def add_test(): 
        st.session_state['num_tests'] += 1
        
    def remove_test(): 
        if st.session_state['num_tests'] > 1: 
            st.session_state['num_tests'] -= 1

    # Render inputs for every active test
    tests_config = []
    for i in range(st.session_state['num_tests']):
        st.subheader(f"Test {i+1}")
        
        # Name Input
        t_name = st.text_input(f"Test Name", value=f"Test {i+1}", key=f"name_{i}")
        
        # Sensitivity & Specificity
        # Using the helper function inside the sidebar context
        sens = synced_input(f"Sensitivity", f"sens_{i}", 0.0, 100.0, 90.0)
        spec = synced_input(f"Specificity", f"spec_{i}", 0.0, 100.0, 80.0)
        
        tests_config.append({"name": t_name, "sensitivity": sens, "specificity": spec})
        st.markdown("---")

    # 3. Action Buttons
    # -----------------
    # We use columns here to place buttons side-by-side cleanly
    b_col1, b_col2 = st.columns(2)
    
    with b_col1:
        st.button("➕ Add Test", on_click=add_test, use_container_width=True)
        
    with b_col2:
        # Only show remove button if we have more than 1 test
        disabled_status = st.session_state['num_tests'] <= 1
        st.button("➖ Remove", on_click=remove_test, disabled=disabled_status, use_container_width=True)

# ==========================================
# MAIN DASHBOARD RENDERING
# ==========================================
# Calculations run after inputs are gathered
results = calculations.run_simulation(N, prev, tests_config)
summary = results['summary']

st.title("Sequential Screening Dashboard")

# ROW 1: Sankey Flow
# ------------------
st.subheader("1. Patient Flow")
st.caption("Visualizes how the population is filtered through sequential tests.")
sankey_fig = visuals.create_sankey(results)
st.plotly_chart(sankey_fig, use_container_width=True)

# ROW 2: Global Metrics
# ---------------------
st.subheader("2. Overall Performance Metrics")
def metric_card(col, label, val):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-val">{val}</div>
    </div>
    """, unsafe_allow_html=True)

# Top metrics split into two rows for readability
r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)
metric_card(r2_col1, "Global Sensitivity", f"{summary['Global Sens']:.1f}%")
metric_card(r2_col2, "Global Specificity", f"{summary['Global Spec']:.1f}%")
metric_card(r2_col3, "Global PPV", f"{summary['Global PPV']:.1f}%")
metric_card(r2_col4, "Global NPV", f"{summary['Global NPV']:.1f}%")

r3_col1, r3_col2, r3_col3, r3_col4 = st.columns(4)
metric_card(r3_col1, "Positive LR (LR+)", f"{summary['Global LR+']:.1f}")
metric_card(r3_col2, "Negative LR (LR-)", f"{summary['Global LR-']:.2f}")
metric_card(r3_col3, "Screen Pos Rate", f"{summary['Screen Pos Rate']:.1f}%")
metric_card(r3_col4, "Screen Neg Rate", f"{summary['Screen Neg Rate']:.1f}%")

st.markdown("---")

# ROW 3: Ground Truth vs Final
# ----------------------------
st.subheader("3. Population Comparison: Truth vs. Final Result")
row3_left, row3_right = st.columns(2)

with row3_left:
    st.markdown("**Start: Ground Truth**")
    fig_truth = visuals.create_ground_truth_waffle(
        summary['Diseased'], summary['Healthy'], 
        title="True Disease Prevalence"
    )
    st.plotly_chart(fig_truth, use_container_width=True)

with row3_right:
    st.markdown("**End: Final Classification**")
    fig_final = visuals.create_waffle_chart(
        summary['Final TP'], summary['Final FP'], 
        summary['Final FN'], summary['Final TN'],
        title="Final Screening Outcome"
    )
    st.plotly_chart(fig_final, use_container_width=True)

st.markdown("---")

# ROW 4+: Individual Steps
# ------------------------
st.subheader("4. Step-by-Step Test Performance")
for step in results['history']:
    st.markdown(f"### {step['test_name']}")
    c_left, c_right = st.columns([1, 2])
    
    with c_left:
        # Display Detailed Step Metrics
        st.markdown(f"""
        **Input N:** {step['input_n']}  
        **Sens:** {step['sens']:.1f}% | **Spec:** {step['spec']:.1f}%
        
        **Outcomes:**
        - <span style='color:#E67E22'><b>TP:</b> {step['TP']}</span>
        - <span style='color:#D32F2F'><b>FN:</b> {step['FN']} (Missed)</span>
        - <span style='color:#FBC02D'><b>FP:</b> {step['FP']} (False Alarm)</span>
        - <span style='color:#43A047'><b>TN:</b> {step['TN']} (Safe)</span>
        
        **Metrics:**
        - Pos Rate: {step['pos_rate']*100:.1f}%
        - LR+: {step['lr_plus']:.1f}
        - LR-: {step['lr_minus']:.2f}
        """, unsafe_allow_html=True)
        
    with c_right:
        # Visual Waffle for this step
        fig_step = visuals.create_waffle_chart(
            step['TP'], step['FP'], step['FN'], step['TN'],
            title=f"Results: {step['test_name']}"
        )
        st.plotly_chart(fig_step, use_container_width=True)
    st.divider()