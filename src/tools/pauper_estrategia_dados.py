# Gera as seções de dados do claude/estrategia_pauper.md (side típico e confrontos por arquétipo). Rodar da pasta de trabalho: python3 tools/pauper_estrategia_dados.py
import json
v=json.load(open('pauper/variacoes.json')); c=json.load(open('pauper/confrontos.json'))
meta=json.load(open('pauper/metagame.json'))
nome_arq={a['slug']:a['nome'] for a in meta['arquetipos']}
fam={}; fnome={}
for f in v['familias']:
  fnome[f['slug']]=f['familia']
  for a,_ in f['arquetipos']: fam[a]=f['slug']
m={}
for k,(w,l,d) in c['m'].items():
  a,b=(fam[nome_arq[x]] for x in k.split('|'))
  if a==b: continue
  for x,y,ww,ll in((a,b,w,l),(b,a,l,w)):
    t=m.setdefault((x,y),[0,0]); t[0]+=ww; t[1]+=ll
out=[]
out.append("## Sideboard típico por variação (cópias, carta, % das listas da variação que a usam)")
for f in v['familias']:
  for x in f['variacoes']:
    s='; '.join(f"{q} {n} {p}" for q,n,p in sorted(x['side'],key=lambda t:-t[2]))
    out.append(f"- {x['nome']} ({x['cores']}, {x['pct']}%, {x['n']}): {s}")
out.append("")
out.append("## Confrontos por arquétipo (DeckSnipe, % de vitória do arquétipo da linha; partidas entre parênteses; só com 20+ partidas)")
for f in v['familias']:
  a=f['slug']
  r=[(fnome[b],t) for (x,b),t in m.items() if x==a and sum(t)>=20]
  r.sort(key=lambda z:-sum(z[1]))
  if r: out.append(f"- {f['familia']}: "+'; '.join(f"{n} {round(100*t[0]/sum(t))} ({sum(t)})" for n,t in r))
open('pauper_estrategia_dados.md','w').write('\n'.join(out)+'\n')
print(len('\n'.join(out)))
