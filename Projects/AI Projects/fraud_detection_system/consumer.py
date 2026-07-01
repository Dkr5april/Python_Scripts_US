Python
from confluent_kafka import Consumer
import json

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'fraud-detection-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['transactions'])

print("Ingestor listening for transactions...")
while True:
    msg = consumer.poll(1.0)
    if msg is None: continue
    data = json.loads(msg.value().decode('utf-8'))
    print(f"Received for processing: {data}")