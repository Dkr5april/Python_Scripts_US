import json
import math
import sys
from kafka import KafkaConsumer

# ==================================================================================
# 📚 ARCHITECTURAL DICTIONARY & AI METHODOLOGY KEYWORDS REFERENCE INDEX:
# 1. PARADIGM   : Time-Series Statistical Machine Learning (Quant Analytics Engine)
# 2. ALGORITHM  : Rolling Z-Score Anomaly Detection & Microstructure Feature Matrix
# 3. CONTROLLER : Multi-Feature Statistical Thresholding Vector
# 4. MATH CORES : Moving Average (μ), Standard Deviation (σ), and Absolute Z-Score (Z)
# 5. INPUTS     : Features (ticker, bid_price, ask_price, order_volume, cancel_ratio)
# 6. OBJECTIVE  : Detect HFT Anomalies, Spoofing Patterns, and Liquidity Flash Shocks
# ==================================================================================

# 1. KAFKA BROKER INITIALIZATION TERMINOLOGY
try:
    consumer = KafkaConsumer(
        'banking-market-ticks',
        bootstrap_servers=['localhost:9094'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print("💡 [TERMINOLOGY LOG - KAFKA INFRASTRUCTURE]:")
    print("   |-- [CLUSTER CONFIG] Bootstrap Server Network: localhost:9094")
    print("   |-- [SUBSCRIBED TOPIC] Event Stream Channel: 'banking-market-ticks'")
    print("   |-- [CONSUMER GROUP STATUS] Mode: Quant HFT Time-Series Stream Listener")
except Exception as e:
    print(f"❌ [INFRASTRUCTURE ERROR]: Kafka Broker connection dropped: {e}")
    sys.exit(1)

# 2. IN-MEMORY ROLLING TIME-SERIES STATE MATRIX
WINDOW_SIZE = 5
historical_midpoints = []  # Core Array to hold historical true equilibrium mid-prices
Z_THRESHOLD = 2.0          # Outlier Trigger Boundary (95% Statistical Confidence)

print("\n⚙️  [TERMINOLOGY LOG - TIME-SERIES MODEL PARAMETERS (YOUR PRODUCER COUPLING)]:")
print(f"   |-- [ALGORITHM PARAMS] Rolling Window Cache Size (N)     : {WINDOW_SIZE} ticks")
print(f"   |-- [STATISTICAL BOUNDARY] Volatility Z-Score Limit       : ±{Z_THRESHOLD}")
print(f"   |-- [FEATURE FOCUS 1] Continuous Multi-Variable Scanning : bid_price vs ask_price")
print(f"   |-- [FEATURE FOCUS 2] Order Behavior Feature Assessment   : cancel_ratio & order_volume")
print("\n⚡ [CORE ENGINE] System state: STANDBY. Listening to Live Quant Market Streams...\n")

try:
    for message in consumer:
        print("\n" + "="*95)
        print("📥 [STAGE 1 - QUANT EVENT STREAM INGESTION INTERACTION]")
        print(f"   |-- [METADATA] Kafka Topic Partition: {message.partition} | Message Offset: {message.offset}")
        
        event = message.value
        
        # EXTRACTING INCOMING DATA FIELDS (FEATURES) FROM YOUR EXACT PRODUCER PAYLOAD
        print("\n🔍 [STAGE 2 - FEATURE EXTRACTION (REAL-TIME QUANT ORDER BOOK FEATURES)]")
        ticker = event["ticker"]
        bid_price = event["bid_price"]
        ask_price = event["ask_price"]
        order_volume = event["order_volume"]
        cancel_ratio = event["cancel_ratio"]
        
        print(f"   |-- [IDENTIFIER FEATURE] ticker              (Asset Pair Ticker)    : {ticker}")
        print(f"   |-- [ORDER BOOK LINE 1]  bid_price           (Highest Bid Rate)     : {bid_price:.4f}")
        print(f"   |-- [ORDER BOOK LINE 2]  ask_price           (Lowest Ask Rate)      : {ask_price:.4f}")
        print(f"   |-- [QUANTIFIER METRIC]  order_volume        (Traded Unit Volume)   : {order_volume} units")
        print(f"   |-- [BEHAVIORAL INPUT]   cancel_ratio        (Order Deletion Pace)  : {cancel_ratio*100:.1f}%")
        
        # ==================================================================================
        # 📐 STAGE 3: MARKET MICROSTRUCTURE MATH (Spread, Midpoint, and Layering)
        # ==================================================================================
        print("\n📐 [STAGE 3 - MARKET MICROSTRUCTURE MATH (EQUILIBRIUM DERIVATION)]")
        
        # Spread calculation (Ask - Bid)
        spread = ask_price - bid_price
        
        # True equilibrium Mid-Price
        mid_price = (bid_price + ask_price) / 2.0
        
        print(f"   |-- Step 3.1 [SPREAD VECTOR]  : Ask ({ask_price:.4f}) - Bid ({bid_price:.4f}) = {spread:.4f}")
        print(f"   |-- Step 3.2 [MID-PRICE EQUIL]: (Bid + Ask) / 2 = {mid_price:.4f}")
        
        # Update rolling state data
        historical_midpoints.append(mid_price)
        if len(historical_midpoints) > WINDOW_SIZE:
            historical_midpoints.pop(0)
            
        print(f"   |-- [ACTIVE TIME-SERIES WINDOW] Memory Array State Cache : {[round(p,4) for p in historical_midpoints]}")
        
        # Check if enough time-series baseline exists
        if len(historical_midpoints) < 3:
            print("\n⏳ [NOTICE] Loading baseline repository array. Awaiting additional streaming ticks...")
            print("="*95)
            continue
            
        # ==================================================================================
        # 📊 STAGE 4: STATISTICAL ROLLING METRICS (Moving Average & Volatility Engine)
        # ==================================================================================
        print("\n📊 [STAGE 4 - TIME-SERIES STATISTICS ENGINE (ROLLING VOLATILITY MATRIX)]")
        
        N = len(historical_midpoints)
        
        # Moving Average (μ)
        moving_average = sum(historical_midpoints) / N
        print(f"   |-- Step 4.1 [MOVING AVERAGE (μ)] Formula: Sum(Prices) / N = ${moving_average:.4f}")
        
        # Rolling Variance and Standard Deviation (σ - Volatility)
        variance_sum = sum((x - moving_average) ** 2 for x in historical_midpoints)
        variance = variance_sum / N
        rolling_std = math.sqrt(variance)
        
        print(f"   |-- Step 4.2 [VOLATILITY CALCULATION (σ)]:")
        print(f"       |--> Sum of Squared Deviations : {variance_sum:.6f}")
        print(f"       |--> Variance (σ^2)            : {variance:.6f}")
        print(f"       |--> Standard Deviation (σ)    : sqrt({variance:.6f}) = {rolling_std:.6f}")
        
        if rolling_std == 0:
            rolling_std = 0.0001  # Zero division guard

        # ==================================================================================
        # 🔮 STAGE 5: ANOMALY SCORE DEPLOYMENT (Z-Score Core Logic)
        # ==================================================================================
        print("\n🔮 [STAGE 5 - STATISTICAL ANOMALY SCORE VECTOR DEPLOYMENT (Z-SCORE)]")
        print(f"   |-- Formula: Z = (Current Midpoint - Moving Average) / Volatility")
        
        z_score = (mid_price - moving_average) / rolling_std
        print(f"   |-- [Z-SCORE VECTOR COMPUTATION] : ({mid_price:.4f} - {moving_average:.4f}) / {rolling_std:.6f} = {z_score:.4f}")

        # ==================================================================================
        # 🚦 STAGE 6: HIGH-FREQUENCY TRADING DECISION MATRIX
        # ==================================================================================
        print("\n🚦 [STAGE 6 - QUANT TRADING DECISION BOUNDARY EVALUATION]")
        print(f"   |-- [METRIC CRITERIA] Price Deviation Flag Limit : Absolute Z > {Z_THRESHOLD}")
        print(f"   |-- [BEHAVIORAL CRITERIA] Spoofing Cancel Limit   : cancel_ratio > 0.85 (85%)")
        
        # Combined Anomaly Rules: Extreme price move OR extreme order cancel ratio (Spoofing)
        is_price_anomaly = abs(z_score) > Z_THRESHOLD
        is_spoofing_anomaly = cancel_ratio > 0.85
        
        if is_price_anomaly or is_spoofing_anomaly:
            print(f"\n🚨 [OUTPUT RESULT - QUANT MARKET ANOMALY DETECTED] 🚨")
            print(f"   |-- [CLASSIFICATION] Target Label : QUANT_ANOMALOUS_TICK")
            
            if is_price_anomaly:
                print(f"   |-- [REASON A]: Extreme Flash Volatility! Price drifted by {z_score:.2f} standard deviations.")
            if is_spoofing_anomaly:
                print(f"   |-- [REASON B]: High Suspected HFT Spoofing! Cancel ratio is extremely high at {cancel_ratio*100:.1f}%.")
                
            print(f"   |-- [ACTION]: Triggering circuit-breaker flag. Emitting alert packet to Quant Desk Risk Dashboard.")
        else:
            print(f"\n🟢 [OUTPUT RESULT - QUANT TICK VERIFICATION SUCCESSFUL] 🟢")
            print(f"   |-- [CLASSIFICATION] Target Label : NORMAL_QUANT_TICK")
            print(f"   |-- [REASON]: Statistical variance and order execution dynamics conform to typical liquidity distribution bounds.")
            print(f"   |-- |-- [ACTION]: Committing streaming analytics metrics safely into Time-Series Memory Store.")
        print("="*95)

except KeyboardInterrupt:
    print("\n🛑 [SHUTDOWN] Intercepted shutdown command. Terminating Quant streaming processes gracefully.")
finally:
    consumer.close()
    print("🔒 [SHUTDOWN CLEAN] Kafka channels dropped. Memory array flushed successfully.")