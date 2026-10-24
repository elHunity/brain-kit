---
name: import-history
description: Learn the user from their past Claude chats — import a claude.ai data export. Triggers on "import my Claude history", "I downloaded my Claude data", "learn from my old chats", "импортируй мою историю Claude", "я скачал экспорт", or the same in any language. Also offer it yourself at the end of the first or second conversation.
---

# Import history

Their past chats with Claude are the fastest way for you to know them. All of it stays on this computer.

## 1. Get the export — the user does this, you guide one step at a time

Say it in the user's language, one step per message, wait for "done":
1. On a computer (not the phone app), open claude.ai → click your initials bottom-left → Settings → Privacy →
   **Export data**.
2. Wait for the email from Anthropic (minutes to hours). The link works for 24 hours and only while signed in to
   Claude in that browser.
3. Click the link, download the zip. Tell me when it's downloaded.

## 2. Unpack — you do this

1. Find the newest zip from Anthropic in the user's Downloads folder (ask before reading Downloads; if unsure which
   file, ask).
2. Run, with the voice environment's Python (exactly this form — it runs without asking):
   Windows: `~/.secondbrain-venv/Scripts/python.exe .claude/scripts/claude_export.py "<zip>" "Files/Claude export"`
   Mac: `~/.secondbrain-venv/bin/python .claude/scripts/claude_export.py "<zip>" "Files/Claude export"`
3. It prints what is inside. Never edit anything in `Files/Claude export/` — it is the raw source.

## 2a. Private chats stay out — ask before reading

Read only `INDEX.md` (titles and dates) first. Say in one line: "Some chats may be private. Tell me which topics,
people or projects to skip — I won't open them." Write the skip list at the top of `Files/Claude export/INDEX.md`
and never open, quote or summarize a skipped chat. If they say "skip everything personal", read only chats that are
clearly about work, study or projects. (A tester refused the whole import for this reason, 24.10.)

## 3. Learn — read in this order, not everything

1. Memory files, if the export has them (anything with "memor" in the name) — Claude's own summary of the user. Gold.
2. Projects (anything with "project" in the name) — what they work on, their instructions to Claude.
3. `Files/Claude export/INDEX.md` — titles and dates. Pick the most frequent themes and the last 3 months.
4. Open only the chats you need. Search by word; don't read hundreds of files.

## 4. Write — in the user's language

- `00-Profile.md`: who they are, work, people and projects that matter, how they like to be answered.
  Mark each line "(from Claude history, check)". Keep `Language:` and `First run:` lines as they are.
- `My rules.md`: rules they gave Claude more than once ("always…", "don't…", "shorter") — with "(from history)".
- `Topics/`: one note per big recurring question, short, linking to the source chats.
- `00-Focus.md`: what they were in the middle of, most recent first.
- Log line in `00-Log.md`, index lines for new notes.

## 5. Show, don't dump

Say in 4–5 short sentences what you learned, then: "What's wrong here?" Fix what they correct, and write each
correction into `My rules.md` or the profile.

Never copy passwords, card or ID numbers from the history into notes, even if they are in old chats.
