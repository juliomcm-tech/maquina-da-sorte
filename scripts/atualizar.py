#!/usr/bin/env python3
"""Máquina da Sorte · robô de resultados (corre no GitHub Actions).

Junta, em dados/resultados.json, os sorteios recentes do EuroMilhões e do
EuroDreams com a tabela oficial de prémios:
  - números: arquivos abertos LottoData (MIT, fonte win2day.at) e Lottochaos (CC BY 4.0);
  - prémios, vencedores na Europa e em Portugal: página oficial dos Jogos Santa Casa.
Corre só depois dos sorteios, poucas vezes por semana. Se uma fonte falhar,
mantém o que já tinha e tenta de novo na próxima execução.
"""
import csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dados" / "resultados.json"
UA = {"User-Agent": "MaquinaDaSorte/1.0 (+github.com; resultados pessoais)"}
DESDE = 20261001  # o HTML já traz o histórico anterior

OPEN = {
    "em": ["https://raw.githubusercontent.com/daowa89/lottery-archive/main/eu/euromillions/results.csv",
           "https://raw.githubusercontent.com/Loisirio/lottochaos-lottery-data/main/data/em.csv"],
    "ed": ["https://raw.githubusercontent.com/Loisirio/lottochaos-lottery-data/main/data/ed.csv"],
}
JSC = {
    "em": "https://www.jogossantacasa.pt/web/ResultsBoard/euromilhoes",
    "ed": "https://www.jogossantacasa.pt/web/ResultsBoard/EuroDreams",
    "m1": "https://www.jogossantacasa.pt/web/ResultsBoard/m1lhao",
}
NTFY = os.environ.get("NTFY_TOPIC", "").strip()
GAME = {
    "em": dict(k=5, N=50, kb=2, B=12, tiers=["5+2", "5+1", "5+0", "4+2", "4+1", "3+2", "4+0", "2+2", "3+1", "3+0", "1+2", "2+1", "2+0"]),
    "ed": dict(k=6, N=40, kb=1, B=5, tiers=["6+1", "6", "5", "4", "3", "2"]),
}


def get(url, enc="utf-8"):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode(enc, errors="replace")


def valid(g, n, b):
    c = GAME[g]
    return (len(n) == c["k"] and len(set(n)) == c["k"] and all(1 <= x <= c["N"] for x in n)
            and len(b) == c["kb"] and len(set(b)) == c["kb"] and all(1 <= x <= c["B"] for x in b))


def open_draws(g):
    """Sorteios recentes dos arquivos abertos (o primeiro que responder)."""
    c = GAME[g]
    for url in OPEN[g]:
        try:
            rows = list(csv.DictReader(io.StringIO(get(url))))
        except Exception as e:
            print(f"[aviso] {g}: {url} -> {e}")
            continue
        out = []
        for r in rows:
            d = int(r["date"].replace("-", ""))
            if d < DESDE:
                continue
            n = sorted(int(r[f"n{i}"]) for i in range(1, c["k"] + 1))
            bkeys = [f"b{i}" for i in range(1, c["kb"] + 1)]
            if not all(k in r for k in bkeys):
                bkeys = [f"s{i}" for i in range(1, c["kb"] + 1)]
            b = sorted(int(r[k]) for k in bkeys)
            if valid(g, n, b):
                out.append({"g": g, "d": d, "n": n, "b": b, "src": url.split("/")[3]})
        return out
    return []


def text(html):
    t = re.sub(r"<[^>]+>", " ", html)
    t = t.replace("&#8364;", "€").replace("&euro;", "€").replace("&#47;", "/").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t).strip()


def euros(s):
    m = re.search(r"€\s*([\d.]+),(\d{2})", s)
    return float(m.group(1).replace(".", "") + "." + m.group(2)) if m else None


def inteiro(s):
    s = re.sub(r"[^\d]", "", s)
    return int(s) if s else None


def jsc_draw(g):
    """Último sorteio na página oficial dos Jogos Santa Casa: data, prémios e (se der) a chave."""
    html = get(JSC[g], "iso-8859-1")
    m = re.search(r"Data do Sorteio\s*-\s*(\d{2})/(\d{2})/(\d{4})", html)
    if not m:
        raise RuntimeError("data do sorteio não encontrada")
    d = int(m.group(3) + m.group(2) + m.group(1))
    c = GAME[g]
    tiers = []
    for block in re.findall(r'<ul class="colums">([\s\S]*?)</ul>', html):
        cells = [text(x) for x in re.findall(r"<li[^>]*>([\s\S]*?)</li>", block)]
        if len(cells) < 5:
            continue
        rk = re.match(r"(\d+)", cells[0])
        if not rk or "Prémio" not in cells[0] and "Premio" not in cells[0]:
            continue
        i = int(rk.group(1)) - 1
        if not 0 <= i < len(c["tiers"]):
            continue
        tiers.append({"t": c["tiers"][i], "pt": inteiro(cells[2]), "w": inteiro(cells[3]), "p": euros(cells[4])})
    if g == "ed":  # 1.º e 2.º prémio são rendas mensais
        for t in tiers:
            if t["t"] in ("6+1", "6"):
                t["p"] = None
    rec = {"g": g, "d": d, "src": "jogossantacasa.pt"}
    if len(tiers) == len(c["tiers"]):
        rec["tiers"] = sorted(tiers, key=lambda t: c["tiers"].index(t["t"]))
        rec["totalWinners"] = sum(t["w"] or 0 for t in tiers)
        rec["jackpotWon"] = bool(rec["tiers"][0]["w"])
    if g == "em":
        j = re.search(r"Previs[aã]o\s*(?:do\s*)?1\.?\s*º?\s*Pr[eé]mio.{0,120}?€\s*([\d.]+(?:,\d{2})?)", text(html))
        if j:
            rec["nextJackpot"] = float(j.group(1).replace(".", "").replace(",", "."))
    # a chave, se a página a mostrar em texto ("Chave ... 1 2 3 4 5 + 6 7")
    k = re.search(r"Chave[^\d]{0,30}((?:\d{1,2}[\s+]+){%d}\d{1,2})" % (c["k"] + c["kb"] - 1), text(html))
    if k:
        nums = [int(x) for x in re.findall(r"\d{1,2}", k.group(1))]
        n, b = sorted(nums[:c["k"]]), sorted(nums[c["k"]:])
        if valid(g, n, b):
            rec["n"], rec["b"] = n, b
    return rec


def jsc_m1():
    """Código M1lhão sorteado (página oficial dos Jogos Santa Casa)."""
    html = get(JSC["m1"], "iso-8859-1")
    m = re.search(r"Data do Sorteio\s*-\s*(\d{2})/(\d{2})/(\d{4})", html)
    c = re.search(r'id="code_m1"[^>]*>\s*([A-Z]{2,4}\s*\d{4,6})\s*<', html) or re.search(r"\b([A-Z]{3}\s?\d{5})\b", text(html))
    if not m or not c:
        raise RuntimeError("código ou data não encontrados")
    return {"d": int(m.group(3) + m.group(2) + m.group(1)), "code": re.sub(r"\s+", "", c.group(1))}


def avisar(novos, m1novo):
    """Envia um aviso para o telemóvel pela app ntfy (só se o segredo NTFY_TOPIC existir)."""
    if not NTFY or not (novos or m1novo):
        return
    nomes = {"em": "EuroMilhões", "ed": "EuroDreams"}
    linhas = []
    for x in novos:
        d = str(x["d"])
        linhas.append(f'{nomes[x["g"]]} {d[6:8]}/{d[4:6]}: {" ".join(map(str, x["n"]))} + {" ".join(map(str, x["b"]))}')
    if m1novo:
        linhas.append(f'M1lhão: {m1novo["code"]}')
    try:
        req = urllib.request.Request("https://ntfy.sh/" + NTFY, data=("\n".join(linhas) + "\nAbre a Máquina da Sorte para conferir.").encode("utf-8"),
                                     headers={"Title": "Saiu o resultado", "Tags": "game_die"})
        urllib.request.urlopen(req, timeout=20)
        print("Aviso enviado.")
    except Exception as e:
        print(f"[aviso] ntfy: {e}")


def main():
    data = {"sorteios": []}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            pass
    idx = {(x["g"], x["d"]): x for x in data.get("sorteios", []) if "g" in x and "d" in x}
    m1 = {x["d"]: x for x in data.get("m1lhao", []) if "d" in x}
    antes_ok = {k for k, x in idx.items() if "n" in x}
    m1novo = None
    try:
        r = jsc_m1()
        if r["d"] not in m1:
            m1novo = r
        m1[r["d"]] = r
        print(f"m1lhão: {r['d']} {r['code']}")
    except Exception as e:
        print(f"[aviso] m1lhão: {e}")
    before = json.dumps(sorted(idx.items(), key=lambda kv: (kv[0][0], kv[0][1])), sort_keys=True, default=str)

    for g in ("em", "ed"):
        for x in open_draws(g):
            old = idx.get((g, x["d"]), {})
            idx[(g, x["d"])] = {**old, **{k: v for k, v in x.items() if k in ("g", "d", "n", "b")}, "src": old.get("src", x["src"])}
        try:
            rec = jsc_draw(g)
        except Exception as e:
            print(f"[aviso] {g}: Jogos Santa Casa -> {e}")
            continue
        old = idx.get((g, rec["d"]), {"g": g, "d": rec["d"]})
        if "n" in old and "n" in rec and (old["n"] != rec["n"] or old["b"] != rec["b"]):
            print(f"[aviso] {g} {rec['d']}: chave da página oficial difere do arquivo aberto; fica a oficial")
        merged = {**old, **rec}
        if "n" not in merged:
            print(f"[aviso] {g} {rec['d']}: prémios lidos mas sem a chave; fica para a próxima execução")
        idx[(g, rec["d"])] = merged
        print(f"{g}: {rec['d']} · {len(rec.get('tiers', []))} escalões")

    # guarda os sorteios com chave válida e também os que só têm prémios (a chave chega depois)
    docs = sorted((x for x in idx.values() if ("n" in x and "b" in x and valid(x["g"], x["n"], x["b"])) or x.get("tiers")),
                  key=lambda x: (x["g"], x["d"]))
    after = json.dumps(sorted(idx.items(), key=lambda kv: (kv[0][0], kv[0][1])), sort_keys=True, default=str)
    novos = [x for k, x in idx.items() if "n" in x and k not in antes_ok and x["d"] >= DESDE and before != "[]"]
    if after == before and OUT.exists() and not m1novo:
        print("Sem novidades.")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    avisar(sorted(novos, key=lambda x: x["d"])[-3:], m1novo)
    OUT.write_text(json.dumps({"atualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sorteios": docs,
                               "m1lhao": sorted(m1.values(), key=lambda x: x["d"])[-60:]},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gravado: {len(docs)} sorteios em dados/resultados.json")


if __name__ == "__main__":
    sys.exit(main())
