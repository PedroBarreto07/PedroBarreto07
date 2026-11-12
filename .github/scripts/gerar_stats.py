"""Gera o card de estatísticas do perfil (claro e escuro) usando a API GraphQL do GitHub.

Uso: GH_TOKEN=... GH_USER=PedroBarreto07 python3 gerar_stats.py dist/
Sem depender de serviços externos (vercel etc.), que saem do ar de vez em quando.
"""
import json
import os
import sys
import urllib.request
from html import escape

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

TEMAS = {
    "escuro": {"titulo": "#E8B84A", "rotulo": "#C9B26A", "valor": "#F4D98B", "icone": "#E8B84A",
               "trilho": "#1E2638", "barras": ["#E8B84A", "#B9892E", "#F4D98B", "#7A6428", "#4A3E1F"]},
    "claro": {"titulo": "#0B1324", "rotulo": "#656D76", "valor": "#0B1324", "icone": "#B9892E",
              "trilho": "#ECE4D2", "barras": ["#8A6210", "#B9892E", "#D9B260", "#0B1324", "#C7BFAE"]},
}


def buscar(token, login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        dados = json.load(r)
    if "errors" in dados:
        raise RuntimeError(dados["errors"])
    u = dados["data"]["user"]
    cc = u["contributionsCollection"]
    repos = u["repositories"]
    langs = {}
    for repo in repos["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:5]
    return {
        "contribuicoes": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "repos": repos["totalCount"],
        "estrelas": sum(r["stargazerCount"] for r in repos["nodes"]),
        "linguagens": [(n, s / total * 100) for n, s in top],
    }


def svg(d, t):
    linhas = [
        ("Contribuições (12 meses)", d["contribuicoes"]),
        ("Commits (12 meses)", d["commits"]),
        ("Pull requests (12 meses)", d["prs"]),
        ("Repositórios públicos", d["repos"]),
        ("Estrelas recebidas", d["estrelas"]),
    ]
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" '
             'aria-label="Estatísticas do GitHub de Pedro Barreto">')
    p.append('<style>text{font-family:"Segoe UI",Ubuntu,"Helvetica Neue",Arial,sans-serif}</style>')
    p.append(f'<text x="25" y="34" font-size="17" font-weight="600" fill="{t["titulo"]}">Estatísticas do GitHub</text>')
    for i, (rot, val) in enumerate(linhas):
        y = 66 + i * 25
        p.append(f'<rect x="25" y="{y - 9}" width="7" height="7" transform="rotate(45 28.5 {y - 5.5})" fill="{t["icone"]}"/>')
        p.append(f'<text x="42" y="{y}" font-size="13" fill="{t["rotulo"]}">{rot}:</text>')
        p.append(f'<text x="250" y="{y}" font-size="13" font-weight="700" fill="{t["valor"]}" text-anchor="end">{val}</text>')
    # linguagens
    x0, w = 280, 190
    p.append(f'<text x="{x0}" y="66" font-size="13" font-weight="600" fill="{t["titulo"]}">Linguagens</text>')
    p.append(f'<rect x="{x0}" y="76" width="{w}" height="8" rx="4" fill="{t["trilho"]}"/>')
    p.append(f'<clipPath id="c"><rect x="{x0}" y="76" width="{w}" height="8" rx="4"/></clipPath><g clip-path="url(#c)">')
    x = x0
    for i, (_, pct) in enumerate(d["linguagens"]):
        lw = w * pct / 100
        p.append(f'<rect x="{x:.2f}" y="76" width="{lw:.2f}" height="8" fill="{t["barras"][i]}"/>')
        x += lw
    p.append('</g>')
    for i, (nome, pct) in enumerate(d["linguagens"]):
        y = 108 + i * 19
        p.append(f'<circle cx="{x0 + 5}" cy="{y - 4}" r="4.5" fill="{t["barras"][i]}"/>')
        p.append(f'<text x="{x0 + 16}" y="{y}" font-size="12" fill="{t["rotulo"]}">{escape(nome)}</text>')
        p.append(f'<text x="{x0 + w}" y="{y}" font-size="12" fill="{t["valor"]}" text-anchor="end">{pct:.1f}%</text>')
    p.append('</svg>')
    return "\n".join(p)


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(destino, exist_ok=True)
    if os.environ.get("STATS_EXEMPLO"):
        d = json.loads(os.environ["STATS_EXEMPLO"])
    else:
        d = buscar(os.environ["GH_TOKEN"], os.environ.get("GH_USER", "PedroBarreto07"))
    for nome, tema in TEMAS.items():
        with open(os.path.join(destino, f"stats-{nome}.svg"), "w", encoding="utf-8") as f:
            f.write(svg(d, tema))
    print("Cards gerados:", d)


if __name__ == "__main__":
    main()
