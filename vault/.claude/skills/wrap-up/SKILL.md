---
name: wrap-up
description: Close the conversation — update focus, log and save a restore point. Triggers on goodbye ("bye", "that's all", "thanks, done", "пока", "всё", "спасибо") or "wrap up", in any language. Do it without being asked when the user says goodbye.
---

# Wrap-up

1. Go through the conversation: decisions, new facts about the user, corrections, open tasks.
   Anything not yet in the notes — save it (see the remember skill). Corrections → `My rules.md`.
2. Rewrite `00-Focus.md`: what we are working on, where we stopped, the next step. Short.
3. One line in `00-Log.md` with today's date and what was done.
4. Save a restore point, silently:
   `git add -A` then `git commit -m "Wrap-up <YYYY-MM-DD>"`. If git says nothing to commit — fine.
   Never push anywhere.
5. Say one line in the user's language: what you remembered, and "next time, just say 'continue'".
