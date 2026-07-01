from confluent_kafka import Consumer
import json
import datetime

# Configuration for mTLS
conf = {
    'bootstrap.servers': 'localhost:9093',
    'group.id': 'fraud-detection-group',
    'auto.offset.reset': 'earliest',
    # mTLS settings
    'security.protocol': 'SSL',
    'ssl.ca.location': 'certs/ca-public-stamp.pem',
    'ssl.certificate.location': 'certs/consumer-cert.pem',
    'ssl.key.location': 'certs/consumer-private.key', 
    'ssl.keystore.location': 'certs/consumer-keystore.jks',
    'ssl.keystore.password': 'password',
    'ssl.truststore.location': 'certs/consumer-truststore.jks',
    'ssl.truststore.password': 'password'
}

consumer = Consumer(conf)
consumer.subscribe(['transactions'])

print("Ingestor listening for secure transactions...")
while True:
    msg = consumer.poll(1.0)
    if msg is None: continue
    data = json.loads(msg.value().decode('utf-8'))
    # FRAUD DETECTION RULES
    is_fraud = False
    reasons = []

    if data['amount'] > 4000:
        is_fraud = True
        reasons.append("High Amount")
    
    if data['location'] == 'High-Risk-Country':
        is_fraud = True
        reasons.append("High-Risk Location")

    if is_fraud:
        print(f"!!! ALERT: Fraud detected for User {data['user_id']}! Reasons: {', '.join(reasons)}")
        # Save to file
        with open("fraud_alerts.log", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {json.dumps(data)} - Reasons: {', '.join(reasons)}\n")
    else:
        print(f"Clean transaction: {data['user_id']} - {data['amount']}")