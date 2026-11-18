"""
Skrypt benchmarkowy do pracy inżynierskiej doDECK.
Mierzy rzeczywiste opóźnienia komunikacji (RTT dla WebSocket i HTTP)
oraz obciążenie procesora i pamięci RAM stacji roboczej.

Uruchomienie:
    python benchmark_performance.py
"""

import time
import json
import hmac
import hashlib
import statistics
import requests
import socketio
import psutil
import os
import sys

# Konfiguracja
SERVER_HOST = "http://127.0.0.1:5000"
NUM_REQUESTS = 100

def get_secret():
    from modules.security import get_or_create_secret
    return get_or_create_secret()

def test_http_latency():
    print(f"\n[1/3] Rozpoczynanie testu opóźnień HTTP REST (próba N={NUM_REQUESTS})...")
    latencies = []
    url = f"{SERVER_HOST}/dispatcher/trigger"
    headers = {"Content-Type": "application/json"}
    payload = {"command": "open_url", "args": "https://example.com"} # bezpieczny test

    for i in range(NUM_REQUESTS):
        start = time.perf_counter()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=2)
            end = time.perf_counter()
            latencies.append((end - start) * 1000.0)
        except Exception as e:
            print(f"Błąd zapytania {i}: {e}")
        time.sleep(0.01)

    return latencies

def test_websocket_latency(secret_key):
    print(f"\n[2/3] Rozpoczynanie testu opóźnień WebSocket + HMAC (próba N={NUM_REQUESTS})...")
    sio = socketio.SimpleClient()
    try:
        sio.connect(SERVER_HOST, transports=['websocket'])
    except Exception as e:
        print(f"Błąd połączenia WebSocket: {e}")
        return []

    latencies = []
    for i in range(NUM_REQUESTS):
        timestamp = str(time.time())
        command = "hotkey"
        args = ""
        raw_string = f"{command}{args}{timestamp}"
        signature = hmac.new(secret_key.encode('utf-8'), raw_string.encode('utf-8'), hashlib.sha256).hexdigest()

        packet = {
            "command": command,
            "args": args,
            "timestamp": timestamp,
            "signature": signature
        }

        start = time.perf_counter()
        sio.emit("trigger_action", packet)
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)
        time.sleep(0.01)

    sio.disconnect()
    return latencies

def print_stats(name, data):
    if not data:
        print(f"{name}: Brak danych pomiarowych.")
        return
    print(f"\n=== Wyniki: {name} ===")
    print(f"Liczba próbek: {len(data)}")
    print(f"Min:           {min(data):.2f} ms")
    print(f"Średnia:       {statistics.mean(data):.2f} ms")
    print(f"Mediana:       {statistics.median(data):.2f} ms")
    print(f"Max:           {max(data):.2f} ms")
    print(f"Odchylenie st: {statistics.stdev(data):.2f} ms")

def measure_resources():
    print("\n[3/3] Badanie zasobów stacji roboczej (CPU i RAM procesu serwera)...")
    current_pid = os.getpid()
    proc = psutil.Process(current_pid)
    
    cpu_samples = []
    ram_samples = []
    
    for _ in range(10):
        cpu_samples.append(proc.cpu_percent(interval=0.2))
        ram_samples.append(proc.memory_info().rss / (1024 * 1024))
        
    print(f"Średnie obciążenie CPU: {statistics.mean(cpu_samples):.2f}%")
    print(f"Średnie zużycie RAM:   {statistics.mean(ram_samples):.2f} MB")

if __name__ == "__main__":
    print("--- ROZPOCZĘCIE BENCHMARKU WYDAJNOŚCIOWEGO doDECK ---")
    secret = get_secret()
    
    http_data = test_http_latency()
    ws_data = test_websocket_latency(secret)
    
    print_stats("HTTP REST", http_data)
    print_stats("WebSocket (doDECK)", ws_data)
    measure_resources()
    print("\n--- ZAKOŃCZONO POMIARY ---")
