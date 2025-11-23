# load_test.py
import requests
import threading

def generate_load():
    while True:
        requests.post("http://helix/predict", json={"input": "test"})

# Start 100 threads
for _ in range(100):
    threading.Thread(target=generate_load).start()