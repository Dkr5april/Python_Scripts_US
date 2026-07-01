class SignalTracker:
    def __init__(self, name, baseline):
        self.signal_name = name
        self.current_score = baseline
        self.history_log = []

    def update_and_boost(self, incoming_value):
        # Adds incoming data and applies an internal structural boost
        self.current_score = self.current_score + incoming_value + 15
        self.history_log.append(incoming_value)


# --- Execution Timeline ---
# 🔴 SET BREAKPOINT HERE (Line 15)
tracker_A = SignalTracker("Alpha_Feed", 100)

tracker_A.update_and_boost(50)
print("Tracking session complete.")  # Your stop sign