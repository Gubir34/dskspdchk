#!/usr/bin/env python3
import os, sys, tempfile, time, random

# --- CLI tuş ve dil seçimi ---
def select_language():
    print("Select language / Dil seçin:")
    print("[1] Türkçe")
    print("[2] English")
    while True:
        choice = input(">>> ")
        if choice == "1":
            return "tr"
        elif choice == "2":
            return "en"
        else:
            print("1 veya 2 seçin / Choose 1 or 2")

LANG = select_language()

TEXT = {
    "tr": {
        "cache_option": "Test modu seçin: [1] Cache, [2] SSD, [3] Ikisi de",
        "prompt_count": "Kaç kez test edilsin? ",
        "seq_write": "{}. test: yazma {} MB...",
        "seq_read": "{}. test: okuma {} MB...",
        "done": "Tamamlandı!",
        "avg": "=== Ortalama ===",
        "elapsed": "Süre",
        "speed": "Hız",
        "score": "Puan (10000 MB/s üzerinden)",
        "progress": "İlerleme",
        "chk_option": "Disk kontrolü yapmak ister misiniz? (E/H)",
        "chk_done": "CHKDSK tamamlandı (simülasyon)",
    },
    "en": {
        "cache_option": "Select test mode: [1] Cache, [2] SSD, [3] Both",
        "prompt_count": "How many times to run test? ",
        "seq_write": "{}. test: writing {} MB...",
        "seq_read": "{}. test: reading {} MB...",
        "done": "Done!",
        "avg": "=== Average ===",
        "elapsed": "Elapsed",
        "speed": "Speed",
        "score": "Score (out of 10000 MB/s)",
        "progress": "Progress",
        "chk_option": "Do you want to run disk check? (Y/N)",
        "chk_done": "CHKDSK completed (simulation)",
    }
}

txt = TEXT[LANG]

# --- Disk test modu ---
def select_mode():
    print(txt["cache_option"])
    while True:
        choice = input(">>> ")
        if choice in ["1","2","3"]:
            return int(choice)
        else:
            print("1-3 arasında seçim yapın / Choose 1-3")

MODE = select_mode()  # 1=cache, 2=SSD, 3=both

# --- CHKDSK simülasyonu ---
def do_chk():
    choice = input(txt["chk_option"]).strip().lower()
    if choice in ['e','y']:
        print(txt["chk_done"])

# --- Yardımcı fonksiyonlar ---
def parse_size(size_str):
    size_str = size_str.strip().upper()
    units = {"B":1,"KB":1000,"MB":1000**2,"GB":1000**3}
    num = ''.join(c for c in size_str if c.isdigit() or c=='.')
    unit = size_str[len(num):] or 'B'
    if unit not in units:
        raise ValueError(f"Unsupported unit: {unit}")
    return int(float(num)*units[unit])

def show_progress(progress, total, bar_len=30):
    filled = int(progress/total * bar_len)
    bar = "#"*filled + "-"*(bar_len-filled)
    print(f"\r[{bar}] {progress}/{total} MB", end="", flush=True)

def write_file(path, size, fill='random', chunk_mb=8):
    chunk = 1024*1024*chunk_mb
    written = 0
    start = time.time()
    with open(path, 'wb') as f:
        while written < size:
            to_write = min(chunk, size - written)
            if fill == 'zero' or MODE==1:
                buf = b'\0'*to_write
            else:
                buf = os.urandom(to_write)
            f.write(buf)
            written += to_write
            show_progress(written//(1024*1024), size//(1024*1024))
    print()
    end = time.time()
    speed = size/(1024*1024)/(end-start)
    return end-start, speed

def read_file(path, chunk_mb=8):
    size = os.path.getsize(path)
    chunk = 1024*1024*chunk_mb
    read = 0
    start = time.time()
    with open(path, 'rb') as f:
        while read < size:
            data = f.read(chunk)
            if not data:
                break
            read += len(data)
            show_progress(read//(1024*1024), size//(1024*1024))
    print()
    end = time.time()
    speed = size/(1024*1024)/(end-start)
    return end-start, speed

# --- Main ---
def main():
    size_input = input("Dosya boyutunu girin (örn 500MB, 1GB): ")
    size = parse_size(size_input)
    temp_dir = tempfile.gettempdir()
    count = int(input(txt["prompt_count"]))

    do_chk()  # opsiyonel CHKDSK

    write_times, write_speeds = [], []
    read_times, read_speeds = [], []

    for i in range(count):
        fname = os.path.join(temp_dir, f"dskspdchkfile_{i+1}.dskspdchkfile")
        print(txt["seq_write"].format(i+1, size_input))
        elapsed, speed = write_file(fname, size)
        write_times.append(elapsed)
        write_speeds.append(speed)

        if MODE != 1:  # Cache sadeceysa okuma atla
            print(txt["seq_read"].format(i+1, size_input))
            elapsed, speed = read_file(fname)
            read_times.append(elapsed)
            read_speeds.append(speed)

        os.remove(fname)

    # Ortalama ve puanlama
    print("\n"+txt["avg"])
    if write_times:
        print(f"{txt['elapsed']} yazma: {sum(write_times)/count:.2f}s, {txt['speed']}: {sum(write_speeds)/count:.2f} MB/s")
    if read_times:
        print(f"{txt['elapsed']} okuma: {sum(read_times)/count:.2f}s, {txt['speed']}: {sum(read_speeds)/count:.2f} MB/s")

    avg_speed = ((sum(write_speeds)/count if write_speeds else 0) + (sum(read_speeds)/count if read_speeds else 0)) / (2 if read_speeds else 1)
    score = min(avg_speed/10000*100, 100)
    print(f"{txt['score']}: {score:.2f}/100")

if __name__ == "__main__":
    main()
