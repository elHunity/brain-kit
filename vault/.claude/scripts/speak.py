# Reads Claude's replies aloud (Claude Code hooks). Windows and macOS.
#   Stop hook:             speak.py          -> reads hook JSON from stdin, starts a detached worker
#   UserPromptSubmit hook: speak.py --stop   -> stops all speech, playing and queued
#   Manual test:           speak.py --say <utf8 text file>
#   Synth only (no sound): speak.py --mp3 <utf8 text file> <out.mp3>
# The voice is picked per chunk by the script of the text (Cyrillic, Hebrew, everything else),
# so a Russian answer is never read by an English voice. Free Microsoft voices (edge-tts), no key.
# Config: speak.json next to this file ("enabled": false = silent). Log: <temp>/secondbrain-speak/log.txt
import asyncio, json, os, re, subprocess, sys, tempfile, threading, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(tempfile.gettempdir(), "secondbrain-speak")
os.makedirs(STATE, exist_ok=True)
STOP_FILE = os.path.join(STATE, "stop")
LOCK = os.path.join(STATE, "play.lock")
LOG = os.path.join(STATE, "log.txt")
WINDOWS = os.name == "nt"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def load_cfg():
    with open(os.path.join(HERE, "speak.json"), encoding="utf-8") as f:
        return json.load(f)


def stop_all():
    with open(STOP_FILE, "w") as f:
        f.write(str(time.time_ns()))


def stopped_since(born):
    try:
        with open(STOP_FILE) as f:
            return int(f.read().strip() or 0) > born
    except (OSError, ValueError):
        return False


# ---------- reading the reply ----------

def user_prompt(entry):
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(b.get("type") == "text" for b in content if isinstance(b, dict))
    return False


def reply_from_transcript(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except ValueError:
                pass
    start = 0
    for i, e in enumerate(entries):
        if user_prompt(e):
            start = i + 1
    # only the final answer: text after the last tool call of the turn
    parts = []
    for e in entries[start:]:
        if e.get("type") != "assistant" or e.get("isSidechain"):
            continue
        for b in e.get("message", {}).get("content", []) or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                parts = []
            elif b.get("type") == "text" and b.get("text", "").strip():
                parts.append(b["text"].strip())
    return "\n\n".join(parts)


# ---------- language ----------

def script_of(text):
    cyr = len(re.findall(r"[Ѐ-ӿ]", text))
    heb = len(re.findall(r"[֐-׿]", text))
    lat = len(re.findall(r"[A-Za-zÀ-ɏ]", text))
    best = max(cyr, heb, lat)
    if best == 0:
        return "default"
    if best == cyr:
        return "cyrillic"
    if best == heb:
        return "hebrew"
    return "default"


# ---------- markdown -> speech ----------

PATH_RE = re.compile(r"(?<!\S)(?:[A-Za-z]:[\\/]|/[a-z]/|~/|\.\.?/)\S+|(?<!\S)[^\s/\\]+(?:[/\\][^\s/\\]+){2,}")
URL_RE = re.compile(r"https?://\S+|www\.\S+")


def to_speech(md, phrases):
    flags = set()

    def code_block(m):
        flags.add("code")
        return "\n"

    t = re.sub(r"```.*?```", code_block, md, flags=re.S)
    t = re.sub(r"<[^>\n]+>", "", t)

    def md_link(m):
        flags.add("link")
        return m.group(1)

    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", md_link, t)
    t = re.sub(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]", lambda m: m.group(2) or m.group(1), t)

    def inline_code(m):
        s = m.group(1)
        if "/" in s or "\\" in s or "http" in s or len(s) > 40:
            flags.add("path")
            return ""
        return s

    t = re.sub(r"`([^`\n]*)`", inline_code, t)

    def drop(kind):
        def f(m):
            flags.add(kind)
            return ""
        return f

    t = URL_RE.sub(drop("link"), t)
    t = PATH_RE.sub(drop("path"), t)

    out = []
    for line in t.split("\n"):
        s = line.strip()
        if not s:
            out.append("")
            continue
        if s.startswith("|"):
            if re.fullmatch(r"[|:\-\s]+", s):
                continue
            s = ", ".join(c.strip() for c in s.strip("|").split("|") if c.strip())
        s = re.sub(r"^#+\s*", "", s)
        s = re.sub(r"^>\s*", "", s)
        s = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", s)
        s = s.replace("**", "").replace("__", "")
        s = re.sub(r"(?<!\w)[*_](\S.*?\S|\S)[*_](?!\w)", r"\1", s)
        s = s.replace("→", " — ").replace("←", " — ")
        s = re.sub(r"[←-⇿☀-➿\U0001F000-\U0001FFFF]", "", s)
        s = re.sub(r"\(\s*\)", "", s)
        s = re.sub(r"\s{2,}", " ", s).strip(" ,;:")
        if not s:
            continue
        if s[-1] not in ".!?:…":
            s += "."
        out.append(s)
    text = "\n".join(out).strip()
    if flags and text:
        lang = phrases.get(script_of(text), phrases.get("default", {}))
        tail = [lang[k] for k in ("link", "path", "code") if k in flags and lang.get(k)]
        if tail:
            text += "\n\n" + " ".join(tail)
    return text


def chunks(text):
    # synthesis returns a whole chunk only: start with one short sentence, grow while earlier ones play
    sents = [s.strip() for s in re.split(r"(?<=[.!?…])\s+|\n+", text) if s.strip()]
    limits = [80, 200, 400, 700]
    cur = ""
    for s in sents:
        limit = limits[0] if limits else 900
        if cur and (len(cur) + len(s) > limit or script_of(cur) != script_of(s)):
            yield cur
            cur = s
            if limits:
                limits.pop(0)
        else:
            cur = (cur + " " + s).strip()
    if cur:
        yield cur


# ---------- synth + play ----------

def profile_language():
    # "Language: X" line in 00-Profile.md, two folders up from this script
    try:
        with open(os.path.join(HERE, "..", "..", "00-Profile.md"), encoding="utf-8") as f:
            m = re.search(r"^Language:\s*(.+?)\s*$", f.read(), re.M)
            return m.group(1).lower() if m else ""
    except OSError:
        return ""


def pick_voice(text, cfg):
    script = script_of(text)
    own = cfg.get("by_language", {}).get(profile_language(), {})
    return own.get(script) or cfg["voices"].get(script) or cfg["voices"]["default"]


def synth(text, cfg, out):
    import edge_tts
    voice = pick_voice(text, cfg)
    asyncio.run(edge_tts.Communicate(text, voice, rate=cfg.get("rate", "+0%")).save(out))


def acquire(born):
    # one speaker at a time across all chats; stale locks (dead worker) expire
    while True:
        if stopped_since(born):
            return False
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) > 30:
                    os.remove(LOCK)
            except OSError:
                pass
            time.sleep(0.2)


def touch_lock():
    try:
        os.utime(LOCK)
    except OSError:
        pass


def play_windows(path, born, alias):
    import ctypes
    mci = ctypes.windll.winmm.mciSendStringW
    buf = ctypes.create_unicode_buffer(64)
    if mci('open "%s" type mpegvideo alias %s' % (path, alias), None, 0, None):
        log("mci open failed " + path)
        return True
    mci("play " + alias, None, 0, None)
    try:
        while True:
            time.sleep(0.15)
            touch_lock()
            if stopped_since(born):
                return False
            mci("status %s mode" % alias, buf, 64, None)
            if buf.value != "playing":
                return True
    finally:
        mci("close " + alias, None, 0, None)


def play_mac(path, born):
    p = subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while p.poll() is None:
        time.sleep(0.15)
        touch_lock()
        if stopped_since(born):
            p.terminate()
            return False
    return True


def play(path, born, alias):
    return play_windows(path, born, alias) if WINDOWS else play_mac(path, born)


def worker(textfile, born):
    born = int(born)
    cfg = load_cfg()
    with open(textfile, encoding="utf-8") as f:
        text = f.read()
    parts = list(chunks(text))
    files = [None] * len(parts)
    ready = [threading.Event() for _ in parts]
    gate = threading.Semaphore(4)

    def prefetch(i, p):
        with gate:
            if not stopped_since(born):
                out = os.path.join(STATE, "%d_%d.mp3" % (born, i))
                try:
                    synth(p, cfg, out)
                    files[i] = out
                except Exception:
                    log("synth failed: " + traceback.format_exc())
        ready[i].set()

    for i, p in enumerate(parts):
        threading.Thread(target=prefetch, args=(i, p), daemon=True).start()
        time.sleep(0.01)
    locked = False
    try:
        locked = acquire(born)
        if not locked:
            return
        for i in range(len(parts)):
            while not ready[i].wait(0.2):
                touch_lock()
                if stopped_since(born):
                    return
            if i == 0:
                log("first audio after %.1fs, %d chunks" % (time.time() - born / 1e9, len(parts)))
            if files[i] and not play(files[i], born, "s%d_%d" % (born % 1000000, i)):
                return
    finally:
        if locked:
            try:
                os.remove(LOCK)
            except OSError:
                pass
        for p in files + [textfile]:
            try:
                if p:
                    os.remove(p)
            except OSError:
                pass


def start(text):
    for name in os.listdir(STATE):  # leftovers of interrupted workers
        p = os.path.join(STATE, name)
        if name.endswith((".mp3", ".txt")) and name != "log.txt" and time.time() - os.path.getmtime(p) > 600:
            try:
                os.remove(p)
            except OSError:
                pass
    born = time.time_ns()
    textfile = os.path.join(STATE, "%d.txt" % born)
    with open(textfile, "w", encoding="utf-8") as f:
        f.write(text)
    if WINDOWS:
        detach = {"creationflags": 0x00000008 | 0x00000200}  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        detach = {"start_new_session": True}
    subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--worker", textfile, str(born)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     close_fds=True, **detach)


def main():
    args = sys.argv[1:]
    if args[:1] == ["--stop"]:
        stop_all()
        return
    if args[:1] == ["--worker"]:
        worker(args[1], args[2])
        return
    cfg = load_cfg()
    phrases = cfg.get("phrases", {})
    if args[:1] in (["--say"], ["--mp3"]):
        with open(args[1], encoding="utf-8") as f:
            text = to_speech(f.read(), phrases)
        if args[0] == "--say":
            start(text)
        else:
            for i, p in enumerate(chunks(text)):
                synth(p, cfg, args[2].replace(".mp3", "_%d.mp3" % i))
                print(i, script_of(p), pick_voice(p, cfg), p[:60])
        return
    if not cfg.get("enabled", True):
        return
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    md = ""
    tp = data.get("transcript_path")
    if tp and os.path.exists(tp):
        md = reply_from_transcript(tp)
    last = (data.get("last_assistant_message") or "").strip()
    if last and last not in md:
        md = (md + "\n\n" + last).strip()
    text = to_speech(md, phrases)
    if text:
        start(text)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("error: " + traceback.format_exc())
