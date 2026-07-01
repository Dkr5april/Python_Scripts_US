# =========================================================================
# THE PARTS OF THE MACHINE
# =========================================================================

class FeatureStore:
    """ROOM 1: The Warehouse memory row."""
    def __init__(self):
        # We start with a default number of 1
        self.memory_row = {"incoming_value": 1} 

class GraphRules:
    """ROOM 2: The permanent multiplier rule."""
    def __init__(self):
        # Our permanent rule multiplier is 2
        self.permanent_multiplier = 2


# =========================================================================
# THE RUNNER TIMELINE (Step-by-Step Data Movement)
# =========================================================================
if __name__ == "__main__":
    
    # --- SETUP PHASE ---
    store = FeatureStore()
    rules = GraphRules()
    
    # =====================================================================
    # 🔴 BREAKPOINT: Place your red dot on the line below!
    # =====================================================================
    live_input = 3   # 1. This is our fresh incoming number
    
    # 📥 STEP 1 & 2: WHAT IS COMING IN (Ingestion Pipeline)
    store.memory_row["incoming_value"] = live_input  # Number 3 overwrites the 1
    
    # 🧮 STEP 3: THE FORMULA SIMULATION (The Collision Math)
    # Formula: Incoming Number (3) x Permanent Rule (2)
    final_score = store.memory_row["incoming_value"] * rules.permanent_multiplier
    
    # 📤 STEP 4: WHAT IS GOING OUT (The Agent Decision)
    if final_score > 5:
        signal_output = "TRIGGER_ALERT"  # (Because 3 x 2 = 6, which is > 5)
    else:
        signal_output = "SIT_IDLE"
        
    # --- PRINT THE RESULT REPORT ---
    print(f"\n📥 Incoming Memory Row Updated To: {store.memory_row['incoming_value']}")
    print(f"🧮 Formula Execution: {store.memory_row['incoming_value']} x {rules.permanent_multiplier} = {final_score}")
    print(f"📤 Final Outgoing Signal: {signal_output}\n")