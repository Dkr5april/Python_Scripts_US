import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

class UnifiedBankingProducer:
    def __init__(self, bootstrap_servers=['localhost:9094']):
        # Initialize a single producer instance with JSON serialization
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("⚡ Unified Enterprise Banking Producer Initialized.")

    def send_event(self, topic_name, payload):
        """Sends a structured message to a specified banking topic"""
        payload['producer_timestamp'] = datetime.utcnow().isoformat()
        self.producer.send(topic_name, value=payload)
        self.producer.flush()
        print(f" [✔] Sent message to Topic: {topic_name}")

    # --- USE CASES 1, 3, 4: AUTHORIZATION STREAM ---
    def generate_auth_event(self):
        return {
            "transaction_id": f"TXN-{random.randint(100000, 999999)}",
            "account_id": f"ACC-{random.randint(1111, 9999)}",
            "amount": round(random.uniform(5.0, 12000.0), 2),
            "merchant_category": random.choice(["6011", "5411", "5812", "7995"]), # ATM, Grocery, Dining, Betting
            "terminal_id": f"TERM-{random.randint(10, 99)}",
            "geo_velocity_kph": random.choice([15, 45, 850]), # 850 kph triggers fraud velocity anomaly
            "typing_speed_ms": random.randint(80, 250)      # Synthetic bots type deterministically fast
        }

    # --- USE CASE 2: LEDGER TRANSFERS (AML) ---
    def generate_ledger_event(self):
        return {
            "transfer_id": f"XFER-{random.randint(55555, 99999)}",
            "source_account": f"ACC-{random.randint(1111, 2222)}",
            "destination_account": f"ACC-{random.randint(8888, 9999)}",
            "amount": round(random.uniform(1000.0, 9500.0), 2), # Layering often hovers right below limits
            "routing_depth": random.randint(1, 7)               # High depth indicates complex laundering networks
        }

    # --- USE CASE 5: QUANT MARKET TICKS ---
    def generate_market_tick(self):
        return {
            "ticker": "EUR_USD",
            "bid_price": round(random.uniform(1.0500, 1.1200), 4),
            "ask_price": round(random.uniform(1.0501, 1.1202), 4),
            "order_volume": random.randint(10000, 500000),
            "cancel_ratio": round(random.uniform(0.01, 0.95), 2)
        }

    # --- USE CASE 6: OMNI-CHANNEL TELEMETRY (CHURN) ---
    def generate_telemetry_event(self):
        return {
            "customer_id": f"CUST-{random.randint(100, 500)}",
            "channel": random.choice(["mobile_app", "web_portal", "call_center"]),
            "action": random.choice(["view_fee_schedule", "delete_bill_pay", "export_statement"]),
            "session_duration_sec": random.randint(10, 600)
        }

    # --- USE CASE 7: CORE INFRASTRUCTURE SYSLOGS ---
    def generate_syslog_event(self):
        return {
            "host": "mainframe-core-01",
            "db_lock_duration_ms": random.randint(2, 4500), # 4500ms lock duration is a heavy systemic log anomaly
            "cpu_utilization": round(random.uniform(12.5, 99.8), 1),
            "thread_count": random.randint(200, 1500)
        }

    # --- USE CASE 8: MACRO INDUSTRIAL NEWS FEED ---
    def generate_news_feed(self):
        return {
            "corporate_id": "CORP-GLOBAL-LOGISTICS",
            "source": "Commercial News Wire",
            "headline_text": random.choice([
                "Quarterly asset revenues remain stable amidst steady consumer demand.",
                "Supply chain blockages force factory operations to stall indefinitely." # High distress text signal
            ])
        }

    # --- USE CASE 9: CAPITAL MARKET SETTLEMENTS ---
    def generate_settlement_event(self):
        return {
            "trade_id": f"TRD-{random.randint(11111, 44444)}",
            "counterparty_id": "CLEARING-HOUSE-NY",
            "settlement_status": random.choice(["MATCHED", "EXCEPTION_MISMATCH", "REJECTED"]),
            "discrepancy_code": random.choice(["NONE", "ERR-FIELD-MISSING", "VAL-DATE-INVALID"])
        }

    # --- USE CASE 10: CUSTOMER SUPPORT TICKETS ---
    def generate_support_ticket(self):
        return {
            "ticket_id": f"TCK-{random.randint(888, 999)}",
            "raw_text": random.choice([
                "I forgot my password and my account is locked out.",
                "My screen says application error code 500 during funds transfer.",
                "Is anyone else receiving this text message asking for my debit card PIN number?"
            ])
        }

# --- LOCAL SIMULATION RUNNER ---
if __name__ == "__main__":
    # Change bootstrap_servers to your active cluster location
    banking_stream = UnifiedBankingProducer(bootstrap_servers=['localhost:9094'])
    
    try:
        while True:
            # Simultaneously feeding the ecosystem with varied data payloads
            banking_stream.send_event("banking-authorizations", banking_stream.generate_auth_event())
            banking_stream.send_event("banking-ledger-transfers", banking_stream.generate_ledger_event())
            banking_stream.send_event("banking-market-ticks", banking_stream.generate_market_tick())
            banking_stream.send_event("banking-omni-telemetry", banking_stream.generate_telemetry_event())
            banking_stream.send_event("banking-core-syslogs", banking_stream.generate_syslog_event())
            banking_stream.send_event("banking-macro-news", banking_stream.generate_news_feed())
            banking_stream.send_event("banking-trade-settlements", banking_stream.generate_settlement_event())
            banking_stream.send_event("banking-support-tickets", banking_stream.generate_support_ticket())
            
            print("-" * 60)
            time.sleep(2) # Pauses for 2 seconds before generating the next streaming event burst
    except KeyboardInterrupt:
        print("\n⏹ Stream Simulation stopped by system administrator.")