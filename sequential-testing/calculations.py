import pandas as pd
import numpy as np

def run_simulation(N, prevalence, tests):
    """
    Core logic for the Sequential Screening Simulator.
    
    SIMULATION LOGIC:
    This function models a "Series" (Sequential) screening strategy.
    - Step 1: Entire population takes Test 1.
    - Step 2: Only those who screen POSITIVE on Test 1 take Test 2.
    - Step 3: Only those who screen POSITIVE on Test 2 take Test 3 (and so on).
    - Screen Negatives (TN/FN) at any stage are removed from the flow.
    
    Args:
        N (int): Total population size.
        prevalence (float): Disease prevalence (0.0 - 100.0).
        tests (list): List of dicts containing 'sensitivity', 'specificity', 'name'.
        
    Returns:
        dict: A fully populated results dictionary with 'summary' and 'history'.
    """
    
    # ---------------------------------------------------------
    # 1. SETUP INITIAL GROUND TRUTH
    # ---------------------------------------------------------
    prev_decimal = prevalence / 100.0
    
    # We round to integers to represent whole people. 
    # This avoids floating point artifacts (e.g., 0.5 people).
    num_diseased = int(round(N * prev_decimal))
    num_healthy = N - num_diseased
    
    # 'current_diseased' and 'current_healthy' represent the 
    # active pool of patients moving to the next test.
    current_diseased = num_diseased
    current_healthy = num_healthy
    
    history = []
    
    # ---------------------------------------------------------
    # 2. RUN SEQUENTIAL TESTS
    # ---------------------------------------------------------
    for i, test in enumerate(tests):
        # Extract inputs
        sens = test['sensitivity'] / 100.0
        spec = test['specificity'] / 100.0
        name = test.get('name', f"Test {i+1}")
        
        # --- A. CALCULATE OUTCOMES FOR THIS STEP ---
        
        # 1. Apply Sensitivity to the Diseased Pool
        # TP = Sick people correctly identified -> They Move Forward
        # FN = Sick people missed -> They Drop Out
        step_tp = int(round(current_diseased * sens))
        step_fn = current_diseased - step_tp 
        
        # 2. Apply Specificity to the Healthy Pool
        # TN = Healthy people correctly identified -> They Drop Out
        # FP = Healthy people incorrectly flagged -> They Move Forward
        step_tn = int(round(current_healthy * spec))
        step_fp = current_healthy - step_tn
        
        # --- B. CALCULATE METRICS FOR THIS STEP ---
        
        total_tested = current_diseased + current_healthy
        total_pos = step_tp + step_fp
        total_neg = step_tn + step_fn
        
        # Rates relative to the input of THIS specific test
        pos_rate = (total_pos / total_tested) if total_tested > 0 else 0
        neg_rate = (total_neg / total_tested) if total_tested > 0 else 0
        
        # Likelihood Ratios (Step Level)
        # LR+ = Sens / (1 - Spec)
        # LR- = (1 - Sens) / Spec
        lr_plus = (sens / (1 - spec)) if (1 - spec) > 0 else 100.0 
        lr_minus = ((1 - sens) / spec) if spec > 0 else 100.0
        
        stage_data = {
            "test_index": i + 1,
            "test_name": name,
            "input_n": total_tested,
            "input_diseased": current_diseased,
            "input_healthy": current_healthy,
            "TP": step_tp,
            "FP": step_fp,
            "TN": step_tn,
            "FN": step_fn,
            "pos_rate": pos_rate,
            "neg_rate": neg_rate,
            "sens": sens * 100,
            "spec": spec * 100,
            "lr_plus": lr_plus,
            "lr_minus": lr_minus
        }
        history.append(stage_data)
        
        # --- C. UPDATE POOL FOR NEXT STEP ---
        # Critical Sequential Logic:
        # Only True Positives and False Positives take the next test.
        current_diseased = step_tp
        current_healthy = step_fp
        
    # ---------------------------------------------------------
    # 3. CALCULATE GLOBAL METRICS
    # ---------------------------------------------------------
    # The survivors after the last loop are the final Screen Positives
    final_tp = current_diseased
    final_fp = current_healthy
    
    # Global Negatives = Everyone filtered out at ANY stage
    final_tn = num_healthy - final_fp
    final_fn = num_diseased - final_tp
    
    # Avoid zero division for global metrics
    global_sens = (final_tp / num_diseased * 100) if num_diseased > 0 else 0
    global_spec = (final_tn / num_healthy * 100) if num_healthy > 0 else 0
    global_ppv = (final_tp / (final_tp + final_fp) * 100) if (final_tp + final_fp) > 0 else 0
    global_npv = (final_tn / (final_tn + final_fn) * 100) if (final_tn + final_fn) > 0 else 0
    
    # Global Likelihood Ratios (based on Net Performance)
    net_sens_d = global_sens / 100.0
    net_spec_d = global_spec / 100.0
    
    global_lr_plus = (net_sens_d / (1 - net_spec_d)) if (1 - net_spec_d) > 0 else 100.0
    global_lr_minus = ((1 - net_sens_d) / net_spec_d) if net_spec_d > 0 else 100.0
    
    # Global Screen Rates (Total population basis)
    screen_pos_rate = ((final_tp + final_fp) / N * 100) if N > 0 else 0
    screen_neg_rate = ((final_tn + final_fn) / N * 100) if N > 0 else 0
    
    results = {
        "summary": {
            "Total N": N,
            "Diseased": num_diseased,
            "Healthy": num_healthy,
            "Final TP": final_tp,
            "Final FP": final_fp,
            "Final TN": final_tn,
            "Final FN": final_fn,
            "Global Sens": global_sens,
            "Global Spec": global_spec,
            "Global PPV": global_ppv,
            "Global NPV": global_npv,
            "Global LR+": global_lr_plus,
            "Global LR-": global_lr_minus,
            "Screen Pos Rate": screen_pos_rate,
            "Screen Neg Rate": screen_neg_rate
        },
        "history": history
    }
    
    return results