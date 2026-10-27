#!/bin/bash
# uso: publicar.sh "mensagem"
set -e
cd /home/claude/precons-commander
git fetch -q origin main
cp -r /home/claude/site/index.html /home/claude/site/sw.js /home/claude/site/README.md /home/claude/site/icons .
git add -A
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "$1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0187eJveCBc9hXgoc8feDh8s"
git push -q origin main
git log --oneline | head -1
