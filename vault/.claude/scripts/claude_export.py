# Unpacks a claude.ai data export (zip) into readable notes for the assistant.
# Usage: python claude_export.py <export.zip or folder> <out folder>
# Writes: <out>/raw/ (the export as is), <out>/conversations/<date> <title>.md (one per chat),
#         <out>/INDEX.md (date, title, messages - newest first). Unknown formats: lists what is inside and stops.
import json, os, re, sys, zipfile

src, out = sys.argv[1], sys.argv[2]
raw = os.path.join(out, "raw")
os.makedirs(raw, exist_ok=True)
if zipfile.is_zipfile(src):
    with zipfile.ZipFile(src) as z:
        z.extractall(raw)
    root = raw
else:
    root = src

files = []
for d, _, names in os.walk(root):
    for n in names:
        files.append(os.path.join(d, n))
print("files in export:")
for f in sorted(files):
    print("  %s  %d KB" % (os.path.relpath(f, root), os.path.getsize(f) // 1024))

conv_file = next((f for f in files if os.path.basename(f) == "conversations.json"), None)
if not conv_file:
    print("no conversations.json - read the files above directly")
    sys.exit(0)

with open(conv_file, encoding="utf-8") as f:
    convs = json.load(f)
if not isinstance(convs, list):
    print("conversations.json is not a list - top keys:", list(convs)[:20])
    sys.exit(0)


def text_of(m):
    t = m.get("text") or ""
    if not t and isinstance(m.get("content"), list):
        t = "\n".join(b.get("text", "") for b in m["content"] if isinstance(b, dict) and b.get("type") == "text")
    return t.strip()


cdir = os.path.join(out, "conversations")
os.makedirs(cdir, exist_ok=True)
rows = []
for c in convs:
    msgs = c.get("chat_messages") or []
    title = (c.get("name") or "untitled").strip() or "untitled"
    date = (c.get("created_at") or "")[:10]
    safe = re.sub(r'[\\/:*?"<>|\n\r\t]', " ", title)[:80].strip()
    name = "%s %s.md" % (date, safe)
    lines = ["# " + title, "", "Date: " + date, ""]
    for m in msgs:
        who = "User" if m.get("sender") == "human" else "Claude"
        t = text_of(m)
        if t:
            lines += ["## " + who, "", t, ""]
    with open(os.path.join(cdir, name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    rows.append((date, title, len(msgs), name))

rows.sort(reverse=True)
with open(os.path.join(out, "INDEX.md"), "w", encoding="utf-8") as f:
    f.write("# Claude chats - newest first\n\n")
    for date, title, n, name in rows:
        f.write("- %s - %s (%d messages) - conversations/%s\n" % (date, title, n, name))
print("%d conversations -> %s" % (len(rows), cdir))
