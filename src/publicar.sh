#!/bin/bash
# uso: publicar.sh "mensagem"
# Copia o site (pasta site/) para o clone do repositório e publica na main.
# Pastas: a deste script (pasta de trabalho); o site em ./site e o clone em ./precons-commander,
# ou o que estiver em PRECONS_SITE e PRECONS_REPO.
# Rodapé do commit (opcional): COAUTOR (ex.: "Claude Opus 5.5 <noreply@anthropic.com>") e SESSAO (link da sessão).
set -e
[ -n "$1" ] || { echo "uso: publicar.sh \"mensagem\"" >&2; exit 1; }
BASE="$(cd "$(dirname "$0")" && pwd)"
SITE="${PRECONS_SITE:-$BASE/site}"
REPO="${PRECONS_REPO:-$BASE/precons-commander}"
RODAPE=""
[ -n "$COAUTOR" ] && RODAPE="Co-Authored-By: $COAUTOR"
[ -n "$SESSAO" ] && RODAPE="${RODAPE:+$RODAPE
}Claude-Session: $SESSAO"
cd "$REPO"
git fetch -q origin main
cp -r "$SITE/index.html" "$SITE/nomes_pt.json" "$SITE/sw.js" "$SITE/README.md" "$SITE/icons" "$SITE/pauper" .
git add -A
if [ -n "$RODAPE" ]; then
  git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "$1" -m "$RODAPE"
else
  git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "$1"
fi
git push -q origin main
git log --oneline | head -1
