---
name: harvest
description: Close the conversation — save everything to notes, update focus, log and save a restore point, so a new chat can continue. Triggers on /harvest, "harvest", "save the chat", "the chat is too long", "wrap up", goodbye ("bye", "that's all", "thanks, done", "пока", "всё", "спасибо"), in any language. Do it without being asked when the user says goodbye.
---

# Harvest (wrap-up)

1. Go through the conversation: decisions, new facts about the user, corrections, open tasks.
   Anything not yet in the notes — save it (see the remember skill). Corrections → `My rules.md`.
2. Rewrite `00-Focus.md`: what we are working on, where we stopped, the next step. Short.
3. One line in `00-Log.md` with today's date and what was done.
4. Save a restore point, silently:
   `git add -A` then `git commit -m "Wrap-up <YYYY-MM-DD>"`. If git says nothing to commit — fine.
   Never push anywhere.
5. Say one line in the user's language: what you remembered, and "next time, just say 'continue'".
   If the chat was long, add: "Open a new chat with the plus at the top of this panel and say 'continue' — a fresh
   chat is faster and uses less of your Claude limit."
