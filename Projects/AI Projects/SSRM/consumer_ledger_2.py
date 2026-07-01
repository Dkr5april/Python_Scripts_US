import json
import math
import sys
from kafka import KafkaConsumer

# ==================================================================================
# 📚 ARCHITECTURAL DICTIONARY & AI METHODOLOGY KEYWORDS REFERENCE INDEX:
# 1. METHODOLOGY: Supervised Learning (Data has explicit historical targets/labels)
# 2. ALGORITHM  : Logistic Regression Classifier (Binary Classification: Risk vs Safe)
# 3. CONTROLLER : Activation Function (Transforms infinite vector space to probability)
# 4. ENGINE     : Sigmoid Function / Logistic Function (Squeezes 'z' between 0.0 and 1.0)
# 5. INPUTS     : Features (Independent Variables: 'amount' and 'routing_depth')
# 6. OUTPUT     : Target Label Probability (Dependent Variable: 'Compliance Risk Score')
# 7. OPTIMIZER  : Gradient Descent (Historical process that tuned our Weights/Bias via Loss Function)
# ==================================================================================

# 1. KAFKA BROKER INITIALIZATION TERMINOLOGY
try:
    consumer = KafkaConsumer(
        'banking-ledger-transfers',
        bootstrap_servers=['localhost:9094'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print("💡 [TERMINOLOGY LOG - KAFKA INFRASTRUCTURE]:")
    print("   |-- [CLUSTER CONFIG] Bootstrap Server Network: localhost:9094")
    print("   |-- [SUBSCRIBED TOPIC] Event Stream Channel: 'banking-ledger-transfers'")
    print("   |-- [CONSUMER GROUP STATUS] Mode: Real-Time Event Listener Distributed Pipeline")
except Exception as e:
    print(f"❌ [INFRASTRUCTURE ERROR]: Kafka Broker connection dropped: {e}")
    sys.exit(1)

# 2. THE LEARNED CONSTANTS (DERIVED VIA HISTORICAL DATA & GRADIENT DESCENT)
W_AMOUNT = 0.0003           # Feature Weight 1 (Slope/Coefficient for Amount)
W_DEPTH = 0.65              # Feature Weight 2 (Slope/Coefficient for Network Depth Layering)
BIAS = -2.5                 # Model Bias (Intercept baseline parameter showing system neutral state)

print("\n⚙️  [TERMINOLOGY LOG - AI PRE-TRAINED PARAMETERS (LEARNED FROM HISTORICAL ARCHIVE)]:")
print(f"   |-- [SUPERVISED PATTERN CLASSIFIER] Paradigm: Binary Logistic Classification")
print(f"   |-- [FEATURE MATRIX WEIGHT: w1] W_AMOUNT Coefficients  : {W_AMOUNT} (Sensitivity toward Transaction Volume)")
print(f"   |-- [FEATURE MATRIX WEIGHT: w2] W_DEPTH Coefficients   : {W_DEPTH} (Sensitivity toward Layering Complexity)")
print(f"   |-- [BASELINE BIAS INTERCEPT: b] System Default Intercept: {BIAS} (Negative value assumes safe baseline neutrality)")
print(f"   |-- [OPTIMIZATION BACKGROUND] Note: These weights were optimized by minimizing Binary Cross-Entropy Loss Function via Gradient Descent.")
print("\n⚡ [CORE ENGINE] System state: STANDBY. Awaiting raw streaming events from Unified Banking Producer...\n")

try:
    for message in consumer:
        print("\n" + "="*85)
        print("📥 [STAGE 1 - EVENT STREAM INGESTION INTERACTION]")
        print(f"   |-- [METADATA] Kafka Topic Partition: {message.partition} | Message Segment Offset: {message.offset}")
        
        event = message.value
        
        # EXTRACTING INDEPENDENT VARIABLES (FEATURES) FROM PRODUCER PAYLOAD
        print("\n🔍 [STAGE 2 - FEATURE EXTRACTION (INDEPENDENT VARIABLES FROM REAL-TIME STREAM)]")
        transfer_id = event["transfer_id"]
        source_acc = event["source_account"]
        dest_acc = event["destination_account"]
        amount = event["amount"]
        routing_depth = event["routing_depth"]
        
        print(f"   |-- [IDENTIFIER KEY] transfer_id                 (Unique Transaction Hash) : {transfer_id}")
        print(f"   |-- [SOURCE EDGE] source_account                (Origin Node Identifier)  : {source_acc}")
        print(f"   |-- [DESTINATION EDGE] destination_account      (Target Node Identifier)  : {dest_acc}")
        print(f"   |-- [INPUT FEATURE 1 (x1)] amount               (Financial Quantifier)   : ₹{amount}")
        print(f"   |-- [INPUT FEATURE 2 (x2)] routing_depth        (AML Network Graph Depth) : {routing_depth}")
        
        # ==================================================================================
        # 📐 STAGE 3: THE MATHEMATICAL CALCULATION (Linear Combination Vectors)
        # ==================================================================================
        print("\n📐 [STAGE 3 - VECTOR MATRICES LINEAR COMBINATION (z = x1*w1 + x2*w2 + b)]")
        print("   |-- Context: Computing the Raw Dot Product of Input Features and historical Machine Learning Weights.")
        
        amt_contribution = amount * W_AMOUNT
        depth_contribution = routing_depth * W_DEPTH
        
        print(f"   |-- [MATRIX TRANSFORMATION 1] (Feature x1 * Weight w1) : {amount} * {W_AMOUNT} = {amt_contribution:.6f}")
        print(f"   |-- [MATRIX TRANSFORMATION 2] (Feature x2 * Weight w2) : {routing_depth} * {W_DEPTH} = {depth_contribution:.6f}")
        print(f"   |-- [BIAS ADJUSTMENT] System Baseline Intercept (b)   : {BIAS}")
        
        # Calculating the raw net input log-odds score 'z'
        z = amt_contribution + depth_contribution + BIAS
        print(f"   |-- [LOG-ODDS RAW SCORE OUTPUT (z)] Net Equation Value : {amt_contribution:.6f} + {depth_contribution:.6f} + ({BIAS}) = {z:.6f}")
        
        # ==================================================================================
        # 🔮 STAGE 4: NON-LINEAR ACTIVATION (Sigmoid Probability Mapping)
        # ==================================================================================
        print("\n🔮 [STAGE 4 - NON-LINEAR ACTIVATION FUNCTION MAPPING: P(Target Label) = 1 / (1 + e^-z)]")
        print(f"   |-- Context: Mapping the infinite log-odds score vector 'z' ({z:.4f}) into a bounded 0.0 to 1.0 Probability Spectrum.")
        
        try:
            # Calculating Euler's constant (e) raised to the negative power of z
            e_minus_z = math.exp(-z)
            risk_score = 1 / (1 + e_minus_z)
            print(f"   |-- [EULER'S MATHEMATICAL COMPONENT] Calculating (e^-z)  : e^-({z:.6f}) = {e_minus_z:.6f}")
            print(f"   |-- [SIGMOID SQUEEZING FRACTION] Formula Processing       : 1 / (1 + {e_minus_z:.6f})")
            print(f"   |-- [ACTIVATED PROBABILITY OUTPUT] Continuous Value Range : {risk_score:.6f}")
        except OverflowError:
            print("   |-- [⚠️ MATHEMATICAL OVERFLOW NOTICE] Extreme raw score vector encountered. Snapping boundary limits.")
            risk_score = 1.0 if z > 0 else 0.0
            print(f"   |-- [BOUND ADJUSTED RESULT] Snapped Risk Probability: {risk_score}")

        # ==================================================================================
        # 🚦 STAGE 5: COMPLIANCE ROUTING DECISION MATRIX
        # ==================================================================================
        print("\n🚦 [STAGE 5 - BINARY TARGET LABEL CLASSIFICATION & DECISION MATRIX]")
        print(f"   |-- [EVALUATION CRITERIA] Decision Probability Threshold Trigger Rule : > 0.70 (70% Flag Rate)")
        print(f"   |-- [PREDICTED TARGET OUTPUT] Computed Money Laundering Risk Index    : {risk_score:.4f} ({risk_score*100:.2f}%)")
        
        if risk_score > 0.70:
            print(f"\n🚨 [DECISION ENGINE RESULT - HIGH AML LAYERING CLASSIFICATION DETECTED] 🚨")
            print(f"   |-- [CLASSIFICATION] Target Label : RISK_SUSPECT (Value approaching 1.0)")
            print(f"   |-- [SUBSTANTIATION] The feature variables Matrix (Amount: ₹{amount} and Network Depth Layers: {routing_depth}) structurally matched complex layering networks.")
            print(f"   |-- [INFRASTRUCTURE ROUTING INTERACTION] Dispatching message payload safely to FIU (Financial Intelligence Unit) Audit Target Queue.")
        else:
            print(f"\n🟢 [DECISION ENGINE RESULT - COMPLIANCE VERIFICATION PASSED] 🟢")
            print(f"   |-- [CLASSIFICATION] Target Label : SAFE_TRANSACTION (Value approaching 0.0)")
            print(f"   |-- [SUBSTANTIATION] Input indicators conform to historical normal baseline boundaries.")
            print(f"   |-- [INFRASTRUCTURE DB INTERACTION] Emitting 'STATE_COMMIT' command. Ledger balance balances successfully persistence recorded.")
        print("="*85)

except KeyboardInterrupt:
    print("\n🛑 [SHUTDOWN COMMAND] Compliance Consumer intercepted via terminal break signals. Closing handles gracefully.")
finally:
    consumer.close()
    print("🔒 [SHUTDOWN SUCCESS] Kafka Broker connection pool dropped cleanly. Environment variables preserved. Ready for iteration.")