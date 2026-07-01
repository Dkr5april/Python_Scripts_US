import json
import numpy as np
from kafka import KafkaConsumer
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest

class DebuggingSSRMConsumer:
    def __init__(self, topic="banking-authorizations", bootstrap_servers=['localhost:9094']):
        print("=" * 80)
        print("⚙️ [DEBUG STEP 1] INITIALIZATION & INFRASTRUCTURE MATRIX SETUP")
        print("=" * 80)
        
        # Connect to the Kafka Broker
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',
            group_id='debugging-fraud-ssrm-group',
            # CHANGE THIS LINE FROM value_serializer TO value_deserializer:
            value_deserializer=lambda x: json.loads(x.decode('utf-8')) 
        )
        print(f" [✔] Connected to Kafka Topic: '{topic}'")
        
        # Operational Domain Boundaries (Used for Min-Max Scaling Formulas)
        self.bounds = {
            "amount": {"min": 5.0, "max": 12000.0},
            "velocity": {"min": 0.0, "max": 1000.0},
            "typing": {"min": 50.0, "max": 300.0}
        }
        print(f" [✔] Domain Bounds Registered: Amount ({self.bounds['amount']}), Velocity ({self.bounds['velocity']})")
        
        # Categorical Index (Used for One-Hot Vector Matrix Mapping)
        self.mcc_categories = ["6011", "5411", "5812", "7995"]
        print(f" [✔] Categorical Dimensions Mapped: {self.mcc_categories}")

        # Initialize ML Architectures
        self.encoder = PCA(n_components=2)
        self.density_scorer = IsolationForest(contamination=0.1, random_state=42)
        
        # Seed historical points to give the model reference clusters
        self._bootstrap_historical_dense_neighborhood()

    def _bootstrap_historical_dense_neighborhood(self):
        print("\n" + "-"*50)
        print("⚙️ [DEBUG STEP 2] BOOTSTRAPPING BASELINE COORDINATE GRID MAP")
        print("-"*50)
        
        mock_historical_data = []
        for _ in range(50):
            amt = np.random.uniform(10, 200)       # Normal low shopping amounts
            vel = np.random.uniform(5, 40)         # Normal human driving speeds
            typ = np.random.uniform(150, 250)      # Normal human typing paces
            mcc = [1, 0, 0, 0]                     # Standard retail category (6011)
            mock_historical_data.append([amt, vel, typ] + mcc)
            
        scaled_history = []
        for row in mock_historical_data:
            s_amt = (row[0] - self.bounds["amount"]["min"]) / (self.bounds["amount"]["max"] - self.bounds["amount"]["min"])
            s_vel = (row[1] - self.bounds["velocity"]["min"]) / (self.bounds["velocity"]["max"] - self.bounds["velocity"]["min"])
            s_typ = (row[2] - self.bounds["typing"]["min"]) / (self.bounds["typing"]["max"] - self.bounds["typing"]["min"])
            scaled_history.append([s_amt, s_vel, s_typ] + row[3:])

        X = np.array(scaled_history)
        
        # Fit the mathematical transformation matrices
        self.encoder.fit(X)
        embeddings = self.encoder.transform(X)
        self.density_scorer.fit(embeddings)
        print(f" [✔] Successfully trained PCA Projection Weights matrix with shape: {self.encoder.components_.shape}")
        print(" [✔] Baseline historical dense cluster points established in memory.")
        print("=" * 80 + "\n")

    def execution_loop(self):
        print("⏳ SYSTEM STATUS: Live listener engine online. Awaiting data packets from Kafka...\n")
        
        for message in self.consumer:
            # STEP 3: DATA INGESTION STATE
            raw_payload = message.value
            print("\n" + "█"*80)
            print("⚙️ [DEBUG STEP 3] PHASE 1 — INGESTION LAYER DETECTED EVENT")
            print("█"*80)
            print(f"   --> Variable 'raw_payload' loaded into memory RAM.")
            print(f"   --> Payload Dictionary Content:\n{json.dumps(raw_payload, indent=4)}")
            
            # STEP 4: MATHEMATICAL TRANSFORMATION STATE
            print("\n" + "-"*50)
            print("⚙️ [DEBUG STEP 4] PHASE 2 — RUNNING MATHEMATICAL SEPARATION FORMULAS")
            print("-"*50)
            
            # 1. Amount Normalization Formula
            raw_amt = raw_payload["amount"]
            scaled_amt = (raw_amt - self.bounds["amount"]["min"]) / (self.bounds["amount"]["max"] - self.bounds["amount"]["min"])
            print(f"   [Math Link] Variable 'scaled_amt'  : ({raw_amt} - 5.0) / (12000.0 - 5.0) = {scaled_amt:.6f}")
            
            # 2. Velocity Normalization Formula
            raw_vel = raw_payload["geo_velocity_kph"]
            scaled_vel = (raw_vel - self.bounds["velocity"]["min"]) / (self.bounds["velocity"]["max"] - self.bounds["velocity"]["min"])
            print(f"   [Math Link] Variable 'scaled_vel'  : ({raw_vel} - 0.0) / (1000.0 - 0.0) = {scaled_vel:.6f}")
            
            # 3. Typing Speed Normalization Formula
            raw_typ = raw_payload["typing_speed_ms"]
            scaled_typ = (raw_typ - self.bounds["typing"]["min"]) / (self.bounds["typing"]["max"] - self.bounds["typing"]["min"])
            print(f"   [Math Link] Variable 'scaled_typ'  : ({raw_typ} - 50.0) / (300.0 - 50.0) = {scaled_typ:.6f}")
            
            # 4. Categorical Index Array Lookup Mapping
            raw_mcc = raw_payload["merchant_category"]
            one_hot_mcc = [1.0 if raw_mcc == cat else 0.0 for cat in self.mcc_categories]
            print(f"   [Index Link] Variable 'one_hot_mcc': String '{raw_mcc}' matched to Boolean array -> {one_hot_mcc}")
            
            # 5. Union Array Concatenation
            final_vector = [scaled_amt, scaled_vel, scaled_typ] + one_hot_mcc
            print(f"\n   ==> STATE CHANGE: 'final_vector' Converted Assembly:\n       {final_vector}")
            
            # STEP 5: LATENT SPACE COORDINATE PROJECTION
            print("\n" + "-"*50)
            print("⚙️ [DEBUG STEP 5] PHASE 3 — SSRM ENCODER WEIGHT MULTIPLICATION")
            print("-"*50)
            
            vector_np = np.array([final_vector])
            print(f"   --> Matrix conversion: Native list cast to NumPy Array. Shape: {vector_np.shape}")
            
            # Execute dot product transformation
            coordinates = self.encoder.transform(vector_np)[0]
            print(f"   [Theory Link] Multiplied matrix vector by Eigenvector weights to squeeze 7 dimensions to 2 dimensions.")
            print(f"   ==> STATE CHANGE: Extracted 2D Latent Map Coordinate Tuple:")
            print(f"       Coordinate X: {coordinates[0]:.6f}")
            print(f"       Coordinate Y: {coordinates[1]:.6f}")
            
            # STEP 6: DENSITY SCORING & INTERPRETATION LOOP
            print("\n" + "-"*50)
            print("⚙️ [DEBUG STEP 6] PHASE 4 — NEIGHBORHOOD DENSITY EVALUATION")
            print("-"*50)
            
            # Query decision trees
            density_flag = self.density_scorer.predict(np.array([coordinates]))[0]
            anomaly_score = self.density_scorer.score_samples(np.array([coordinates]))[0]
            
            print(f"   --> Variable 'anomaly_score' value: {anomaly_score:.6f} [Density Scale: -1.0 to 0.0]")
            print(f"   --> Variable 'density_flag' state  : {density_flag} [-1 = Sparse/Isolated Void, 1 = Dense Safe Zone]")
            
            if density_flag == 1:
                print("\n   🟢 [FINAL IDENTIFICATION RESULT: SECURE]")
                print("       Analysis: Coordinates match high-density clusters of baseline transactions. No alert generated.")
            else:
                print("\n   🚨 [FINAL IDENTIFICATION RESULT: SYSTEM FRAUD ANOMALY TRIGGERED]")
                print("       Analysis: Coordinate point is isolated in a low-density void. Dispatching security protocol.")
            
            print("█"*80 + "\n")

if __name__ == "__main__":
    debugger = DebuggingSSRMConsumer()
    debugger.execution_loop()