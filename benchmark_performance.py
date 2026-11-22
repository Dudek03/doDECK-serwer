"""
Skrypt benchmarkowy do pracy inżynierskiej doDECK.
Mierzy rzeczywiste opóźnienia komunikacji (RTT dla WebSocket i HTTP)
oraz obciążenie procesora, pamięci RAM, uchwytów i wątków stacji roboczej.

Uruchomienie:
    python benchmark_performance.py
    lub z podaniem adresu IP serwera w sieci LAN:
    python benchmark_performance.py --host http://192.168.1.100:5000
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
import argparse

# Domyślna konfiguracja
DEFAULT_SERVER_HOST = "http://127.0.0.1:5000"
NUM_REQUESTS = 100


def get_secret():
    try:
        from modules.security import get_or_create_secret
        return get_or_create_secret()
    except Exception as e:
        print(f"[WARN] Nie udało się zaimportować get_or_create_secret: {e}")
        return ""


def test_http_latency(server_host: str):
    print(f"\n[1/3] Rozpoczynanie testu opóźnień HTTP REST (próba N={NUM_REQUESTS})...")
    latencies = []
    url = f"{server_host}/dispatcher/trigger"
    headers = {"Content-Type": "application/json"}
    payload = {"command": "hotkey", "args": "shift"}  # bezpieczny test (nie otwiera okien przeglądarki)

    session = requests.Session()  # model HTTP/1.1 Keep-Alive
    for i in range(NUM_REQUESTS):
        start = time.perf_counter()
        try:
            resp = session.post(url, json=payload, headers=headers, timeout=2)
            end = time.perf_counter()
            if resp.status_code == 200:
                latencies.append((end - start) * 1000.0)
            else:
                print(f"Błąd zapytania {i}: kod {resp.status_code}")
        except Exception as e:
            print(f"Błąd zapytania {i}: {e}")
        time.sleep(0.01)

    return latencies


def test_websocket_latency(server_host: str, secret_key: str):
    print(f"\n[2/3] Rozpoczynanie testu opóźnień WebSocket + HMAC (próba N={NUM_REQUESTS})...")
    sio = socketio.SimpleClient()
    try:
        sio.connect(server_host, transports=['websocket', 'polling'])
    except Exception as e:
        print(f"Błąd połączenia WebSocket z {server_host}: {e}")
        return []

    latencies = []
    for i in range(NUM_REQUESTS):
        timestamp = str(time.time())
        command = "hotkey"
        args = "shift"
        raw_string = f"{command}{args}{timestamp}"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            raw_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

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


def find_server_process():
    """Wyszukuje działający proces roboczy serwera doDECK (serwer.py, run.py lub DoDeckServer.exe)."""
    current_pid = os.getpid()
    candidates = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if p.pid == current_pid:
                continue
            name = (p.info.get('name') or '').lower()
            cmd = " ".join(p.info.get('cmdline') or []).lower()
            if "dodeckserver" in name or "serwer.py" in cmd or "run.py" in cmd:
                candidates.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not candidates:
        return None

    # Zwracamy proces o największym zużyciu pamięci (główny proces roboczy, w przypadku relodera Flask)
    candidates.sort(key=lambda x: x.info['memory_info'].rss if x.info.get('memory_info') else 0, reverse=True)
    return candidates[0]


def measure_resources(server_host: str = DEFAULT_SERVER_HOST):
    print("\n[3/3] Badanie zasobów stacji roboczej (CPU, RAM RSS, uchwyty, wątki)...")
    server_proc = find_server_process()
    if server_proc:
        print(f"Znaleziono aktywny proces roboczy serwera: PID {server_proc.pid} ({server_proc.name()})")
        target_proc = server_proc
    else:
        print("Nie wykryto oddzielnego procesu serwera (serwer.py / run.py / DoDeckServer.exe).")
        print("Mierzę zasoby bieżącego środowiska wykonawczego...")
        target_proc = psutil.Process(os.getpid())

    # --- FAZA 1: Stan bezczynności (Idle) ---
    print(" -> [Faza 1/2] Próbkowanie w stanie spoczynku (Idle, brak zapytań przez 3s)...")
    idle_cpu = []
    idle_ram = []
    # Pierwsze wywołanie cpu_percent inicjalizuje licznik
    target_proc.cpu_percent(interval=None)
    for _ in range(6):
        time.sleep(0.5)
        try:
            idle_cpu.append(target_proc.cpu_percent(interval=None))
            idle_ram.append(target_proc.memory_info().rss / (1024 * 1024))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break

    try:
        idle_handles = target_proc.num_handles() if hasattr(target_proc, 'num_handles') else 'N/A'
    except Exception:
        idle_handles = 'N/A'

    try:
        idle_threads = target_proc.num_threads()
    except Exception:
        idle_threads = 'N/A'

    # --- FAZA 2: Stan aktywnego obciążenia (Active Load) ---
    print(" -> [Faza 2/2] Generowanie aktywnego obciążenia roboczego (symulacja ciągłego sterowania 50 req/s przez 4s)...")
    import threading
    stop_load = threading.Event()
    active_cpu = []
    active_ram = []

    def load_generator():
        session = requests.Session()
        endpoint = f"{server_host}/api/system/status"
        # Sprawdzamy czy /api/system/status odpowiada, jeśli nie, odpytujemy stronę główną
        try:
            r = session.get(endpoint, timeout=1)
            target_url = endpoint if r.status_code == 200 else server_host
        except Exception:
            target_url = server_host

        while not stop_load.is_set():
            try:
                session.get(target_url, timeout=1)
            except Exception:
                pass
            time.sleep(0.02)  # ~50 zapytań na sekundę

    load_thread = threading.Thread(target=load_generator, daemon=True)
    load_thread.start()

    # Próbkujemy podczas trwania obciążenia
    target_proc.cpu_percent(interval=None)
    for _ in range(8):
        time.sleep(0.5)
        try:
            active_cpu.append(target_proc.cpu_percent(interval=None))
            active_ram.append(target_proc.memory_info().rss / (1024 * 1024))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break

    stop_load.set()
    load_thread.join(timeout=1.0)

    try:
        active_handles = target_proc.num_handles() if hasattr(target_proc, 'num_handles') else 'N/A'
    except Exception:
        active_handles = 'N/A'

    try:
        active_threads = target_proc.num_threads()
    except Exception:
        active_threads = 'N/A'

    # Obliczenia statystyczne
    mean_idle_cpu = statistics.mean(idle_cpu) if idle_cpu else 0.0
    mean_idle_ram = statistics.mean(idle_ram) if idle_ram else 0.0

    mean_active_cpu = statistics.mean(active_cpu) if active_cpu else 0.0
    max_active_cpu = max(active_cpu) if active_cpu else 0.0
    mean_active_ram = statistics.mean(active_ram) if active_ram else 0.0

    print("\n" + "="*80)
    print(" ZESTAWIENIE ZASOBÓW STACJI ROBOCZEJ (odpowiednik Tab. 4.3)")
    print("="*80)
    print(f"{'Parametr stacji roboczej':<28} | {'Stan spoczynku (Idle)':<22} | {'Aktywne obciążenie (Active)':<24}")
    print("-" * 80)
    print(f"{'Obciążenie procesora (CPU)':<28} | {mean_idle_cpu:.2f}%{'':<17} | {mean_active_cpu:.2f}% (pik: {max_active_cpu:.2f}%)")
    print(f"{'Pamięć prywatna (RAM RSS)':<28} | {mean_idle_ram:.2f} MB{'':<14} | {mean_active_ram:.2f} MB")
    print(f"{'Liczba uchwytów (Handles)':<28} | {str(idle_handles):<22} | {str(active_handles):<24}")
    print(f"{'Liczba wątków (Threads)':<28} | {str(idle_threads):<22} | {str(active_threads):<24}")
    print("="*80)


def print_comparison_table(ws_data, http_data):
    if not ws_data and not http_data:
        print("Brak danych pomiarowych do wygenerowania tabeli.")
        return

    print("\n" + "="*70)
    print(" ZESTAWIENIE WYNIKÓW BENCHMARKU OPÓŹNIEŃ (odpowiednik Tab. 4.2)")
    print("="*70)
    print(f"{'Parametr statystyczny':<30} | {'WebSocket + HMAC':<18} | {'HTTP POST':<15}")
    print("-" * 70)

    def get_stats(arr):
        if not arr:
            return None
        return {
            'min': min(arr),
            'mean': statistics.mean(arr),
            'median': statistics.median(arr),
            'max': max(arr),
            'stdev': statistics.stdev(arr) if len(arr) > 1 else 0.0
        }

    ws_s = get_stats(ws_data)
    http_s = get_stats(http_data)

    rows = [
        ("Wartość minimalna (Min)", 'min'),
        ("Wartość średnia (Mean)", 'mean'),
        ("Mediana (Median)", 'median'),
        ("Wartość maksymalna (Max)", 'max'),
        ("Odchylenie standardowe (σ)", 'stdev')
    ]

    for label, key in rows:
        ws_val = f"{ws_s[key]:.2f} ms" if ws_s else "N/A"
        http_val = f"{http_s[key]:.2f} ms" if http_s else "N/A"
        print(f"{label:<30} | {ws_val:<18} | {http_val:<15}")
    print("="*70)


def check_server_online(server_host: str) -> bool:
    try:
        r = requests.get(server_host, timeout=1.5)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="doDECK Benchmark Wydajnościowy")
    parser.add_argument("--host", default=DEFAULT_SERVER_HOST, help="Adres serwera doDECK (domyślnie: http://127.0.0.1:5000)")
    args = parser.parse_args()

    print("--- ROZPOCZĘCIE BENCHMARKU WYDAJNOŚCIOWEGO doDECK ---")
    print(f"Docelowy serwer: {args.host}")

    server_online = check_server_online(args.host)
    if not server_online:
        print(f"\n[UWAGA] Serwer doDECK pod adresem {args.host} nie odpowiada.")
        print("Aby zmierzyć opóźnienia RTT, uruchom serwer w osobnym terminalu:")
        print("   python serwer.py (lub uruchom DoDeckServer.exe)")
        print("Pomiary sieciowe zostaną pominięte, przechodzę do badania zasobów stacji roboczej...")
        http_data = []
        ws_data = []
    else:
        secret = get_secret()
        if not secret:
            print("[OSTRZEŻENIE] Brak klucza sesji. Upewnij się, że serwer doDECK został zainicjalizowany.")

        http_data = test_http_latency(args.host)
        ws_data = test_websocket_latency(args.host, secret)
        print_comparison_table(ws_data, http_data)

    measure_resources(args.host)
    print("\n--- ZAKOŃCZONO POMIARY ---")
