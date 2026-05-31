import numpy as np
from scipy.optimize import minimize

# ==========================================
# GLOBAL CONFIGURATION (Dynamic Synchronization)
# ==========================================
GLOBAL_CHANNELS = 4
LAMBDA_MAX = 5.0

# ==========================================
# CORE LOGIC MODULES
# ==========================================

def process_tri_state_signals(incoming_signal_array):
    """Maps packet signals to tri-state flags (-1: erasure, 0: idle, 1: healthy)."""
    # Fix: np.select preserves explicit tracking of all three states
    conditions = [incoming_signal_array == -1, incoming_signal_array == 0, incoming_signal_array == 1]
    choices = [-1, 0, 1]
    return np.select(conditions, choices, default=0)

def objective_function(missing_flat_values, observed_data, missing_mask):
    """Minimizes second-order acceleration (kinetic strain)."""
    full_trajectory = observed_data.copy()
    full_trajectory[missing_mask] = missing_flat_values.reshape(-1, GLOBAL_CHANNELS)
    accelerations = np.diff(full_trajectory, n=2, axis=0)
    return np.sum(accelerations**2)

def run_ss138_engine(raw_data, packet_flags):
    """Primary execution pipeline with dynamic boundary adaptation."""
    missing_mask = (packet_flags == -1)
    sanitized_data = raw_data.copy()
    sanitized_data[missing_mask] = np.nan
    
    # 2. Optimization with Linear Initial Guess
    # Replaces flat zeros with a progressive guess to speed up solver convergence
    missing_count = np.sum(missing_mask)
    initial_guess = np.linspace(0, 1, missing_count * GLOBAL_CHANNELS)
    
    result = minimize(
        objective_function, 
        initial_guess, 
        args=(sanitized_data, missing_mask), 
        method='SLSQP'
    )
    
    final_trajectory = sanitized_data.copy()
    final_trajectory[missing_mask] = result.x.reshape(missing_count, GLOBAL_CHANNELS)
    return final_trajectory

# ==========================================
# VERIFICATION TEST (Dynamic Synchronization)
# ==========================================
if __name__ == "__main__":
    # Test data: 12 steps, 4 dimensions
    simulated_signals = np.array([1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1], dtype=np.int32)
    
    # Fix: Syncing data length directly to signal input length
    TOTAL_STEPS = len(simulated_signals)
    raw_data = np.random.rand(TOTAL_STEPS, GLOBAL_CHANNELS)
    
    final_output = run_ss138_engine(raw_data, simulated_signals)
    
    print("=== SS138 PROTOCOL: FINALIZED EXECUTION ===")
    for i in range(len(final_output)):
        vec = final_output[i]
        formatted_vec = ", ".join([f"{v:6.2f}" for v in vec])
        print(f"Step {i:02d} | Vector: [{formatted_vec}]")
