import json
import time
import random
from confluent_kafka import Producer

# Configuration for mTLS
conf = {
    'bootstrap.servers': 'localhost:9093',
    'security.protocol': 'SSL',
    'ssl.ca.location': 'certs/ca-public-stamp.pem',
    'ssl.certificate.location': 'certs/producer-cert.pem',
    'ssl.key.location': 'certs/producer-private.key', # Ensure you have this private key extracted
    'ssl.keystore.location': 'certs/producer-keystore.jks',
    'ssl.keystore.password': 'password',
    'ssl.truststore.location': 'certs/producer-truststore.jks',
    'ssl.truststore.password': 'password'
}

producer = Producer(conf)
topic = 'transactions'

def generate_transaction():
    return {
        "user_id": random.randint(1000, 9999),
        "amount": round(random.uniform(10.0, 5000.0), 2),
        "location": random.choice(['USA', 'UK', 'India', 'High-Risk-Country']),
        "device": random.choice(['mobile', 'desktop'])
    }

print("Starting Transaction Simulator...")
while True:
    data = generate_transaction()
    producer.produce(topic, json.dumps(data).encode('utf-8'))
    producer.flush()
    print(f"Sent: {data}")
    time.sleep(2) # Send a transaction every 2 seconds