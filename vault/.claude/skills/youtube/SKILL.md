---
name: youtube
description: Break down a YouTube video into a note — what it says, the key ideas, what is useful for the user. Triggers when the user drops a YouTube link (youtube.com, youtu.be, shorts), says "break down this video", "what's in this video", "разбери видео", "о чём это видео", or the same in any language. Several links — one note per video.
---

# YouTube video → note

1. Get the text — you do this, silently:
   Windows: `~/.secondbrain-venv/Scripts/python.exe .claude/scripts/youtube.py "<link>"`
   Mac: `~/.secondbrain-venv/bin/python .claude/scripts/youtube.py "<link>"`
   It prints title, channel, length, description and the full speech with times. If it says "Captions: none" —
   tell the user in one line that this video has no text track, and ask for another video or their own summary.
   Never invent what the video says.
2. Save the raw text word for word to `Inbox/<video title>.md` (with the link on top). Never shorten it.
3. Write `Notes/<short title> (<channel>).md` in the user's language:
   - one line: what this video is and who made it, with the link;
   - the main point in two or three sentences;
   - key ideas — each with the time in the video, like (12:40), so the user can jump there;
   - what is weak, old or just selling something — say it plainly;
   - what is useful for this user, judged by `00-Profile.md` and `00-Focus.md`; if nothing — say so;
   - link back to the raw text in `Inbox/`.
4. Log line in `00-Log.md`, index line in `00-Index.md`.
5. Answer in the chat in 3–4 short sentences: the main point and what is useful for them. Offer nothing else.

Speech recognition on auto captions gets names wrong (brands, tools, people). If a name looks odd, say "the video
calls it X — may be misheard" instead of guessing.
