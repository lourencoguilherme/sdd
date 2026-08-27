#!/usr/bin/env python3
"""refinar.py — orquestrador de refino barato para SDD, via Gemini CLI.

Objetivo: tirar do Claude o trabalho caro do refino (gerar/reescrever spec) e
das análises. O loop roda em CÓDIGO chamando o Gemini CLI (tier grátis/barato,
sem API key — usa o login já configurado do `gemini`). O Claude fica só como
revisor/aprovador da candidata — revisar custa muito menos que gerar.

Dois modos:

  refine   Gera uma SPEC candidata a partir de um alvo + contexto, com um loop
           de teto RÍGIDO em código (linhas/critérios/ciclos). Escreve
           `<spec>.candidate.md` ao lado do alvo — NUNCA sobrescreve a aprovada.

  analyze  Análise barata de uma SPEC existente (tamanho, nº de critérios,
           aderência ao teto, riscos, sugestão de decomposição). Imprime um
           relatório curto — para o Claude não gastar tokens analisando.

Sem dependências além da stdlib e do binário `gemini` no PATH.

Exemplos:
  refinar.py analyze changes/.../02-workflows-n8n-agente/SPEC.md
  refinar.py refine  changes/.../02-workflows-n8n-agente/SPEC.md \
                     --context CLAUDE.md --context sdd/sdd-settings.yaml \
                     --max-lines 400 --max-criteria 8 --max-cycles 1
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GWT_RE = re.compile(r"\b(given|when|then|dado|quando|então|entao)\b", re.IGNORECASE)


def die(msg: str, code: int = 1) -> "None":
    print(f"erro: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ensure_gemini() -> str:
    exe = shutil.which("gemini")
    if not exe:
        die("gemini CLI não encontrado no PATH. Instale/logue o Gemini CLI primeiro.", 127)
    return exe


def gemini(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Chama o Gemini CLI em modo não-interativo e devolve o texto (stdout)."""
    exe = ensure_gemini()
    try:
        out = subprocess.run(
            [exe, "-m", model, "-p", prompt],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        die(f"gemini falhou (rc={e.returncode}): {e.stderr.strip()[:500]}")
    # O CLI às vezes emite um aviso de 256-cores no stderr; ignoramos.
    text = out.stdout.strip()
    # Remove cercas de código markdown que o modelo às vezes envolve na resposta.
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


def read_context(paths: list[str]) -> str:
    blocks = []
    for p in paths:
        fp = Path(p)
        if fp.is_file():
            blocks.append(f"\n\n===== CONTEXTO: {p} =====\n{fp.read_text(encoding='utf-8')}")
        else:
            print(f"aviso: contexto não encontrado, ignorando: {p}", file=sys.stderr)
    return "".join(blocks)


def count_metrics(text: str) -> dict:
    lines = text.count("\n") + 1 if text else 0
    gwt = len(GWT_RE.findall(text))
    headings = len(re.findall(r"(?m)^#{1,3} ", text))
    return {"lines": lines, "gwt": gwt, "headings": headings}


# --------------------------------------------------------------------------- #
# analyze
# --------------------------------------------------------------------------- #
def cmd_analyze(args: argparse.Namespace) -> int:
    spec = Path(args.spec)
    if not spec.is_file():
        die(f"SPEC não encontrada: {spec}")
    content = spec.read_text(encoding="utf-8")
    m = count_metrics(content)

    prompt = (
        "Você é um revisor de specs de engenharia. Analise a SPEC abaixo e "
        "responda de forma CURTA e objetiva, em português, cobrindo:\n"
        "1. Ela cabe no orçamento de refino? (teto: "
        f"{args.max_lines} linhas, {args.max_criteria} critérios de aceite). "
        f"Métricas medidas: {m['lines']} linhas, ~{m['gwt']} refs Given/When/Then.\n"
        "2. Onde há inchaço/repetição que pode ser cortado.\n"
        "3. Deveria ser decomposta? Se sim, sugira 2-4 sub-changes.\n"
        "4. Os 3 maiores riscos técnicos não cobertos.\n"
        "Não reescreva a spec; só analise.\n\n"
        f"===== SPEC: {spec} =====\n{content}"
    )
    report = gemini(prompt, model=args.model)

    fits = m["lines"] <= args.max_lines and m["gwt"] <= args.max_criteria * 3
    print(f"# Análise de refino — {spec}")
    print(f"- linhas: {m['lines']} (teto {args.max_lines})")
    print(f"- refs Given/When/Then: {m['gwt']} (teto ~{args.max_criteria} critérios)")
    print(f"- seções: {m['headings']}")
    print(f"- dentro do teto: {'sim' if fits else 'NÃO — considerar decompor'}")
    print(f"- modelo (barato): {args.model}\n")
    print(report)
    return 0


# --------------------------------------------------------------------------- #
# refine
# --------------------------------------------------------------------------- #
def cmd_refine(args: argparse.Namespace) -> int:
    target = Path(args.spec)
    base = target.read_text(encoding="utf-8") if target.is_file() else ""
    ctx = read_context(args.context)

    policy = (
        f"POLÍTICA DE REFINO (obrigatória): a SPEC final deve ter no máximo "
        f"~{args.max_lines} linhas e no máximo {args.max_criteria} critérios de "
        "aceite (Given/When/Then). Se o escopo não couber, NÃO infle — em vez "
        "disso, adicione ao final uma seção '## Decompor' sugerindo sub-changes. "
        "Seja denso e sem repetição. Responda APENAS com a SPEC.md completa em "
        "markdown, nada além dela."
    )

    # 1) rascunho
    draft = gemini(
        f"{policy}\n\nTarefa: refine/complete a SPEC abaixo mantendo o formato SDD "
        f"(frontmatter + critérios em Given/When/Then).{ctx}\n\n"
        f"===== SPEC BASE: {target} =====\n{base or '(vazia — gere do zero a partir do contexto)'}",
        model=args.model,
    )

    # 2) até N ciclos de crítico->revisão, com teto verificado em CÓDIGO
    for cycle in range(1, args.max_cycles + 1):
        m = count_metrics(draft)
        within = m["lines"] <= args.max_lines and m["gwt"] <= args.max_criteria * 3
        if within:
            break
        critique = gemini(
            "Você é um crítico de specs. A SPEC abaixo excede o teto "
            f"({m['lines']}>{args.max_lines} linhas ou {m['gwt']} refs GWT > "
            f"{args.max_criteria} critérios). Aponte em bullets objetivos o que "
            "cortar/condensar SEM perder decisões técnicas, e o que mover para "
            "uma seção '## Decompor'. Seja breve.\n\n" + draft,
            model=args.model,
        )
        draft = gemini(
            f"{policy}\n\nReescreva a SPEC abaixo aplicando ESTAS correções do "
            f"crítico:\n{critique}\n\nResponda apenas com a SPEC.md corrigida.\n\n" + draft,
            model=args.model,
        )
        print(f"[ciclo {cycle}] revisado", file=sys.stderr)

    out = target.with_suffix(".candidate.md")
    out.write_text(draft + "\n", encoding="utf-8")
    m = count_metrics(draft)
    fits = m["lines"] <= args.max_lines and m["gwt"] <= args.max_criteria * 3
    report = {
        "candidate": str(out),
        "lines": m["lines"],
        "gwt_refs": m["gwt"],
        "within_budget": fits,
        "model": args.model,
        "note": "candidata gerada; revise e promova sobre a SPEC.md se aprovar."
                if fits else
                "candidata AINDA acima do teto — considere decompor (ver seção '## Decompor').",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Refino/análise de spec barato via Gemini CLI (SDD).")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"modelo Gemini (default: {DEFAULT_MODEL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="análise barata de uma SPEC existente")
    a.add_argument("spec")
    a.add_argument("--max-lines", type=int, default=400)
    a.add_argument("--max-criteria", type=int, default=8)
    a.set_defaults(func=cmd_analyze)

    r = sub.add_parser("refine", help="gera uma SPEC candidata com teto em código")
    r.add_argument("spec")
    r.add_argument("--context", action="append", default=[], help="arquivo de contexto (repetível)")
    r.add_argument("--max-lines", type=int, default=400)
    r.add_argument("--max-criteria", type=int, default=8)
    r.add_argument("--max-cycles", type=int, default=1, help="ciclos de crítico->revisão (default: 1)")
    r.set_defaults(func=cmd_refine)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
