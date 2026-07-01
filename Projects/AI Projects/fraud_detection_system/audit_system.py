import subprocess
import os
import time

# Directory where your 15 files are stored
CERTS_DIR = "certs"

# Registry of all 15 files relative to the CERTS_DIR
ALL_FILES = [
    ("Root CA Key", "ca-private-stamp.key", "KEY", None),
    ("Root CA Cert", "ca-public-stamp.pem", "CERT", None),
    ("Root CA Serial", "ca-public-stamp.srl", "RAW", None),
    ("Broker Keystore", "kafka-broker-keystore.jks", "JKS", None),
    ("Broker CSR", "kafka-broker.csr", "RAW", None),
    ("Broker Cert", "kafka-broker-cert.pem", "CERT", "ca-public-stamp.pem"),
    ("Broker Truststore", "broker-truststore.jks", "JKS", None),
    ("Producer Keystore", "producer-keystore.jks", "JKS", None),
    ("Producer CSR", "producer.csr", "RAW", None),
    ("Producer Cert", "producer-cert.pem", "CERT", "ca-public-stamp.pem"),
    ("Producer Truststore", "producer-truststore.jks", "JKS", None),
    ("Consumer Keystore", "consumer-keystore.jks", "JKS", None),
    ("Consumer CSR", "consumer.csr", "RAW", None),
    ("Consumer Cert", "consumer-cert.pem", "CERT", "ca-public-stamp.pem"),
    ("Consumer Truststore", "consumer-truststore.jks", "JKS", None),
]

def run_file_audit():
    print(f"\n{'--- PHASE 1: FILE INTEGRITY AUDIT ---':^70}")
    print(f"{'FILE NAME':<40} | {'STATUS':<12} | {'DETAILS'}")
    print("-" * 75)
    
    for desc, filename, ftype, ca_file in ALL_FILES:
        full_path = os.path.join(CERTS_DIR, filename)
        
        if not os.path.exists(full_path):
            print(f"{filename:<40} | {'FAILED':<12} | File missing")
            continue
            
        status = "PASSED"
        details = "OK"
        
        # Verify Signatures if CA is required
        if ftype == "CERT" and ca_file:
            ca_full_path = os.path.join(CERTS_DIR, ca_file)
            cmd = f"openssl verify -CAfile \"{ca_full_path}\" \"{full_path}\""
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if "OK" not in res.stdout:
                status = "FAILED"
                details = "Signature Mismatch"
        
        # Verify JKS Integrity
        elif ftype == "JKS":
            cmd = f"keytool -list -keystore \"{full_path}\" -storepass password"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode != 0:
                status = "FAILED"
                details = "Keystore Error"
        
        print(f"{filename:<40} | {status:<12} | {details}")

def run_ssl_connectivity_audit(host="localhost", port=9093):
    print(f"\n{'--- PHASE 2: SSL CONNECTIVITY AUDIT ---':^70}")
    print(f"Connecting to {host}:{port}...")
    
    # Use openssl to initiate a handshake
    cmd = f"openssl s_client -connect {host}:{port} -verify 1"
    
    try:
        # We pipe 'QUIT' to close the connection immediately
        res = subprocess.run("echo QUIT | " + cmd, shell=True, capture_output=True, text=True)
        
        if "Verify return code: 0 (ok)" in res.stderr:
            print("STATUS: PASSED | SSL Handshake successful and certificate verified.")
        else:
            print("STATUS: FAILED | SSL Handshake/Verification failed.")
            # Print a clean error snippet
            error_msg = res.stderr.splitlines()[-1] if res.stderr else "Unknown SSL Error"
            print(f"Error: {error_msg}")
    except Exception as e:
        print(f"STATUS: FAILED | Could not reach broker: {e}")

if __name__ == "__main__":
    run_file_audit()
    time.sleep(1)
    run_ssl_connectivity_audit()