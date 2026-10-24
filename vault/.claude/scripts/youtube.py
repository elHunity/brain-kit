# youtube.py <link or video id> [lang]
# Prints a YouTube video's title, channel, date and full captions as "[mm:ss] text" lines. No key, no extra installs.
# Method: YouTube's own player endpoint with the iOS app client - the web caption URL needs a token since 2025,
# other clients return no tracks. The auto-generated track is preferred: manual tracks may skip on-screen speech.
import json, re, sys, urllib.request

UA = "com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3_2 like Mac OS X;)"
CLIENT = {"clientName": "IOS", "clientVersion": "20.10.4", "deviceMake": "Apple", "deviceModel": "iPhone16,2",
          "osName": "iPhone", "osVersion": "18.3.2.22D82", "hl": "en"}


def video_id(s):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/)([\w-]{11})", s)
    return m.group(1) if m else s.strip()


def get(url, body=None):
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: youtube.py <link or id> [lang]")
    vid, lang = video_id(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else "")
    body = json.dumps({"context": {"client": CLIENT}, "videoId": vid, "contentCheckOk": True, "racyCheckOk": True})
    j = json.loads(get("https://www.youtube.com/youtubei/v1/player?prettyPrint=false", body.encode()))
    d, mf = j.get("videoDetails", {}), j.get("microformat", {}).get("playerMicroformatRenderer", {})
    tracks = j.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    print("# " + d.get("title", ""))
    print("- Link: https://www.youtube.com/watch?v=" + vid)
    print("- Channel: " + d.get("author", ""))
    print("- Published: %s | Length: %ss | Views: %s" % (mf.get("publishDate", ""), d.get("lengthSeconds", ""),
                                                       d.get("viewCount", "")))
    if not tracks:
        print("- Captions: none (status %s). Ask the user for a short summary or a different video."
              % j.get("playabilityStatus", {}).get("status"))
        sys.exit(2)
    pool = [t for t in tracks if lang and t["languageCode"].split("-")[0] == lang.split("-")[0]] or tracks
    track = next((t for t in pool if t.get("kind") == "asr"), pool[0])
    print("- Captions: %s %s" % (track["languageCode"], "auto" if track.get("kind") == "asr" else "manual"))
    print("- Description: " + d.get("shortDescription", "").replace("\n", " ")[:1500])
    print()
    events = json.loads(get(track["baseUrl"] + "&fmt=json3")).get("events", [])
    for e in events:
        text = re.sub(r"\s+", " ", "".join(s.get("utf8", "") for s in e.get("segs", []))).strip()
        if text:
            s = e.get("tStartMs", 0) // 1000
            print("[%02d:%02d] %s" % (s // 60, s % 60, text))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
