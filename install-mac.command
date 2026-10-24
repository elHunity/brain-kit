#!/bin/bash
# Second Brain installer for macOS.
# Run from Terminal:  bash ~/Downloads/brain-kit/install-mac.command   (works even without the "run" permission)
# Installs programs with Homebrew (the standard Mac installer), asks before each one,
# copies the second brain folder to ~/Documents/SecondBrain and opens it.
set -u

KIT="$(cd "$(dirname "$0")" && pwd)"
BRAIN="$HOME/Documents/SecondBrain"
VENV="$HOME/.secondbrain-venv"

ask() {  # ask "question" -> true on y/Y
  local a
  read -r -p "  $1 [y/n] " a
  [[ "$a" =~ ^[Yy] ]]
}

echo
echo " =============================================="
echo "   Second Brain - setup"
echo " =============================================="
echo
echo " This will install a few free programs from their official makers"
echo " and set up your second brain. It asks before each step."
echo " Nothing about you is sent to the person who gave you this."
echo
read -r -p " Press Enter to start... " _

echo
echo " --- Step 1 of 4: programs ---"
for p in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  [ -x "$p" ] && eval "$("$p" shellenv)"
done
if ! command -v brew >/dev/null 2>&1; then
  echo " Homebrew is the standard installer for Mac programs. It will ask for your Mac password"
  echo " (you won't see it as you type - that's normal) and may install Apple's developer tools."
  if ask "Install Homebrew?"; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    for p in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      [ -x "$p" ] && eval "$("$p" shellenv)"
    done
  fi
fi
if ! command -v brew >/dev/null 2>&1; then
  echo " Without Homebrew this setup can't install programs. Install it from https://brew.sh and run this again."
  exit 1
fi

cask() {  # cask <brew name> <app name in /Applications> <what it is>
  if [ -d "/Applications/$2.app" ] || brew list --cask "$1" >/dev/null 2>&1; then
    echo " $3: already installed."
  elif ask "Install $3?"; then
    brew install --cask "$1"
  else
    echo " Skipped."
  fi
}
cask visual-studio-code "Visual Studio Code" "VS Code - the window where you talk to Claude"
cask obsidian "Obsidian" "Obsidian - shows your notes nicely, free"
cask wispr-flow "Wispr Flow" "Wispr Flow - voice typing, free 2,000 words a week"
if ! command -v git >/dev/null 2>&1 || ! git --version >/dev/null 2>&1; then
  brew install git
fi
PY="$(brew --prefix)/bin/python3"
if [ ! -x "$PY" ]; then
  echo " Python - needed for the voice."
  brew install python
fi

echo
echo " --- Step 2 of 4: your second brain folder ---"
if [ -f "$BRAIN/AGENTS.md" ]; then
  echo " Found an existing second brain in $BRAIN - keeping your notes, not touching it."
else
  mkdir -p "$BRAIN"
  cp -R "$KIT/vault/." "$BRAIN/"
  echo " Created $BRAIN"
  echo
  echo " Which language should it speak with you?"
  echo "   1 - English    2 - Russian    3 - Hebrew    4 - other"
  read -r -p "  Type a number and press Enter: " n
  case "$n" in
    2) lang="Russian" ;;
    3) lang="Hebrew" ;;
    4) read -r -p "  Type your language in English: " lang ;;
    *) lang="English" ;;
  esac
  printf 'Language: %s\n' "$lang" >> "$BRAIN/00-Profile.md"
  git -C "$BRAIN" init -q
  git -C "$BRAIN" config user.name "Second Brain"
  git -C "$BRAIN" config user.email "second-brain@localhost"
  git -C "$BRAIN" add -A
  git -C "$BRAIN" commit -q -m "Start" && echo " Restore points: on."
fi

echo
echo " --- Step 3 of 4: the voice ---"
if [ -x "$VENV/bin/python" ]; then
  echo " Voice: already set up."
elif [ -x "$PY" ]; then
  "$PY" -m venv "$VENV" && "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check edge-tts \
    && echo " Voice: ready. Say \"voice off\" to the assistant to turn it off." \
    || echo " The voice could not be installed - check the internet and run this again."
else
  echo " Python not found - the assistant will answer in text only."
fi

echo
echo " --- Step 4 of 4: opening ---"
CODE="$(command -v code || echo "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")"
if [ -x "$CODE" ]; then
  "$CODE" --install-extension anthropic.claude-code --force
else
  echo " VS Code not found - install it, then add the \"Claude Code\" extension from its Extensions panel."
fi
[ -x "$VENV/bin/python" ] && "$VENV/bin/python" "$KIT/setup/obsidian_register.py" "$BRAIN"
# "open" hands off to macOS and returns at once; the "code <folder>" CLI hung on a screenless test Mac.
# CI (GitHub test Mac) has no screen: don't open windows there.
if [ -z "${CI:-}" ]; then
  open "obsidian://open?vault=SecondBrain" 2>/dev/null
  open -a "Visual Studio Code" "$BRAIN" 2>/dev/null
fi

echo
echo " =============================================="
echo "   Done. What's next:"
echo "   1. If VS Code asks \"Do you trust the authors of the files in this folder?\" -"
echo "      click \"Trust Folder & Continue\"."
echo "   2. Open Claude: the orange spark icon at the top right of VS Code."
echo "      The \"Chat\" panel on the right is Microsoft Copilot, not Claude - close it."
echo "   3. Sign in with your Claude account - Pro or higher."
echo "   4. Say or type \"hi\"."
echo "   To speak instead of typing: Wispr Flow, or Mac dictation:"
echo "   turn it on once in System Settings - Keyboard - Dictation,"
echo "   then press the Microphone key on the top row."
echo "   Read \"Welcome\" in Obsidian for the rest."
echo " =============================================="
echo
