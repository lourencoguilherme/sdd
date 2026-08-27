#!/usr/bin/env python3
"""router.py — roteador adaptativo de modelos para tasks do SDD (CLI-first).

Decide, POR TIPO DE TASK do SDD, o modelo mais barato que ainda dá conta, e só
escala para um modelo mais forte se o barato falhar uma validação objetiva
(feita em código). Usa consumo de tokens para gerenciar o refino e sair mais
rápido: o caminho feliz para no modelo barato e nunca toca no caro.

Backends são CLIs já autenticadas (sem gateway, sem chave de API nova):
  - gemini  (gemini CLI)  — camada barata/grátis (default)
  - claude  (claude CLI)  — camada premium; `--output-format json` reporta tokens reais
  - codex/openai          — plugáveis quando instalados/logados (hoje ausentes)

Uso:
  router.py run --task draft   --spec changes/.../SPEC.md --context CLAUDE.md
  router.py run --task analyze --spec changes/.../SPEC.md
  router.py backends            # lista o que está disponível

A saída inclui um relatório: qual backend/modelo resolveu, quantos ciclos,
tokens (reais quando disponíveis, estimados caso contrário) e se escalou.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

GWT_RE = re.compile(r"\b(given|when|then|dado|quando|então|entao)\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Backends (CLIs)
# --------------------------------------------------------------------------- #
@dataclass
class Result:
    text: str
    backend: str
    model: str
    in_tokens: int = 0
    out_tokens: int = 0
    estimated: bool = True  # True quando os tokens foram estimados, não reportados


def _strip_fences(t: str) -> str:
    t = re.sub(r"^```[a-zA-Z]*\n", "", t.strip())
    t = re.sub(r"\n```\s*$", "", t)
    return t.strip()


def _est_tokens(s: str) -> int:
    return max(1, len(s) // 4)  # ~4 chars/token


def call_gemini(prompt: str, model: str) -> Result:
    exe = shutil.which("gemini")
    if not exe:
        raise RuntimeError("gemini CLI ausente")
    out = subprocess.run([exe, "-m", model, "-p", prompt],
                         capture_output=True, text=True, check=True)
    text = _strip_fences(out.stdout)
    # gemini CLI não reporta tokens no stdout → estimamos.
    return Result(text, "gemini", model,
                  in_tokens=_est_tokens(prompt), out_tokens=_est_tokens(text), estimated=True)


def call_claude(prompt: str, model: str) -> Result:
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("claude CLI ausente")
    out = subprocess.run(
        [exe, "-p", prompt, "--model", model, "--output-format", "json"],
        capture_output=True, text=True, check=True,
    )
    it = ot = 0
    text = out.stdout.strip()
    try:
        data = json.loads(out.stdout)
        text = _strip_fences(str(data.get("result", "")))
        usage = data.get("usage") or {}
        it = int(usage.get("input_tokens", 0) or 0)
        ot = int(usage.get("output_tokens", 0) or 0)
        real = it > 0 or ot > 0
    except (json.JSONDecodeError, ValueError):
        text = _strip_fences(text)
        real = False
    if not (it or ot):
        it, ot = _est_tokens(prompt), _est_tokens(text)
        real = False
    return Result(text, "claude", model, in_tokens=it, out_tokens=ot, estimated=not real)


BACKENDS = {
    "gemini": call_gemini,
    "claude": call_claude,
    # "codex": call_codex,   # plugar quando a CLI existir
}


def available_backends() -> dict:
    return {name: bool(shutil.which(name)) for name in ("gemini", "claude", "codex", "openai")}


# --------------------------------------------------------------------------- #
# Política por task-type do SDD: escada barato -> premium
# --------------------------------------------------------------------------- #
@dataclass
class Step:
    backend: str
    model: str


@dataclass
class TaskPolicy:
    steps: list[Step]              # ordem: mais barato primeiro
    validates: bool = False        # se True, valida em código e faz early-exit/escala
    max_cycles: int = 1            # ciclos crítico->revisão por step (só se validates)
    token_budget: int = 120_000    # teto de tokens acumulados para a task


# Modelos: gemini-2.5-flash (barato) / gemini-2.5-pro (médio) / claude haiku|sonnet.
POLICIES: dict[str, TaskPolicy] = {
    "analyze":  TaskPolicy([Step("gemini", "gemini-2.5-flash")], validates=False, token_budget=40_000),
    "critique": TaskPolicy([Step("gemini", "gemini-2.5-flash")], validates=False, token_budget=40_000),
    "draft":    TaskPolicy([Step("gemini", "gemini-2.5-flash"),
                            Step("gemini", "gemini-2.5-pro"),
                            Step("claude", "sonnet")], validates=True, max_cycles=1, token_budget=150_000),
    "refine":   TaskPolicy([Step("gemini", "gemini-2.5-flash"),
                            Step("claude", "sonnet")], validates=True, max_cycles=1, token_budget=150_000),
    "decompose": TaskPolicy([Step("gemini", "gemini-2.5-pro"),
                             Step("claude", "sonnet")], validates=False, token_budget=120_000),
    "verify":   TaskPolicy([Step("gemini", "gemini-2.5-pro"),
                            Step("claude", "sonnet")], validates=False, token_budget=120_000),
}


def resolve_step(step: Step, fallbacks: dict) -> Step | None:
    """Se o backend do step não existe, tenta cair para um disponível."""
    if fallbacks.get(step.backend):
        return step
    # fallback simples: qualquer backend disponível, mantendo o intento
    for name in ("gemini", "claude"):
        if fallbacks.get(name):
            return Step(name, "gemini-2.5-flash" if name == "gemini" else "sonnet")
    return None


# --------------------------------------------------------------------------- #
# Validação em código (o "juiz" da escada)
# --------------------------------------------------------------------------- #
def metrics(text: str) -> dict:
    return {"lines": (text.count("\n") + 1 if text else 0),
            "gwt": len(GWT_RE.findall(text))}


def within_budget(text: str, max_lines: int, max_criteria: int) -> bool:
    m = metrics(text)
    return m["lines"] <= max_lines and m["gwt"] <= max_criteria * 3


# --------------------------------------------------------------------------- #
# Prompts por task
# --------------------------------------------------------------------------- #
def build_prompt(task: str, spec_text: str, ctx: str, max_lines: int, max_criteria: int) -> str:
    policy = (f"POLÍTICA: a SPEC final deve ter no máximo ~{max_lines} linhas e "
              f"no máximo {max_criteria} critérios (Given/When/Then). Se não couber, "
              "adicione uma seção '## Decompor' em vez de inflar. Denso, sem repetição.")
    if task in ("draft", "refine"):
        return (f"{policy}\nRefine/complete a SPEC mantendo formato SDD (frontmatter + "
                f"critérios GWT). Responda APENAS com a SPEC.md em markdown.{ctx}\n\n"
                f"===== SPEC BASE =====\n{spec_text or '(vazia — gere do contexto)'}")
    if task == "analyze":
        return ("Analise a SPEC abaixo em PT, curto: cabe no teto "
                f"({max_lines} linhas/{max_criteria} critérios)? o que cortar? decompor? "
                f"3 maiores riscos técnicos. Não reescreva.\n\n===== SPEC =====\n{spec_text}")
    if task == "critique":
        return ("Critique a SPEC em bullets objetivos: o que cortar/condensar sem perder "
                f"decisões, o que mover para '## Decompor'. Breve.\n\n{spec_text}")
    if task == "decompose":
        return ("Proponha 2-4 sub-changes independentes para a SPEC abaixo, cada uma com "
                f"escopo e critérios enxutos. PT.\n\n===== SPEC =====\n{spec_text}")
    if task == "verify":
        return ("Verifique se a SPEC é implementável e internamente consistente; liste "
                f"lacunas e contradições. PT, curto.\n\n===== SPEC =====\n{spec_text}")
    raise ValueError(f"task desconhecida: {task}")


# --------------------------------------------------------------------------- #
# Runner adaptativo
# --------------------------------------------------------------------------- #
def run_task(task: str, spec_path: Path, context: list[str],
             max_lines: int, max_criteria: int) -> dict:
    if task not in POLICIES:
        raise SystemExit(f"task inválida: {task} (use: {', '.join(POLICIES)})")
    pol = POLICIES[task]
    avail = available_backends()
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""
    ctx = "".join(f"\n\n===== CONTEXTO: {p} =====\n{Path(p).read_text(encoding='utf-8')}"
                  for p in context if Path(p).is_file())

    spent_in = spent_out = 0
    trail: list[dict] = []
    final: Result | None = None

    for raw in pol.steps:
        step = resolve_step(raw, avail)
        if step is None:
            continue
        prompt = build_prompt(task, spec_text, ctx, max_lines, max_criteria)
        res = BACKENDS[step.backend](prompt, step.model)
        spent_in += res.in_tokens; spent_out += res.out_tokens
        final = res

        ok = True
        if pol.validates:
            ok = within_budget(res.text, max_lines, max_criteria)
            # um ciclo opcional de crítico->revisão no MESMO backend barato
            cyc = 0
            while not ok and cyc < pol.max_cycles:
                crit = BACKENDS[step.backend](
                    f"A SPEC excede o teto ({max_lines} linhas/{max_criteria} critérios). "
                    f"Aponte cortes objetivos e o que mover para '## Decompor'.\n\n{res.text}",
                    step.model)
                res = BACKENDS[step.backend](
                    f"Reescreva aplicando estes cortes:\n{crit.text}\n\nApenas a SPEC.md.\n\n{res.text}",
                    step.model)
                spent_in += crit.in_tokens + res.in_tokens
                spent_out += crit.out_tokens + res.out_tokens
                final = res; cyc += 1
                ok = within_budget(res.text, max_lines, max_criteria)

        trail.append({"backend": step.backend, "model": step.model,
                      "passed_validation": ok, "estimated_tokens": res.estimated})

        # early-exit: passou a validação (ou task sem validação) → para no barato
        if ok:
            break
        if spent_in + spent_out > pol.token_budget:
            trail[-1]["stopped"] = "token_budget_excedido"
            break
        # senão: escala para o próximo step (mais forte)

    # grava candidata para tasks que produzem spec
    out_path = None
    if task in ("draft", "refine") and final:
        out_path = str(spec_path.with_suffix(".candidate.md"))
        Path(out_path).write_text(final.text + "\n", encoding="utf-8")

    m = metrics(final.text) if final else {"lines": 0, "gwt": 0}
    return {
        "task": task,
        "resolved_by": {"backend": final.backend, "model": final.model} if final else None,
        "escalated": len(trail) > 1,
        "ladder": trail,
        "tokens": {"input": spent_in, "output": spent_out, "total": spent_in + spent_out,
                   "note": "reais quando o backend reporta (claude json); senão estimados ~4c/token"},
        "budget": pol.token_budget,
        "spec_metrics": m,
        "candidate": out_path,
        "output": None if out_path else (final.text if final else ""),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Roteador adaptativo de modelos para tasks SDD (CLI-first).")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backends", help="lista backends disponíveis")
    b.set_defaults(func=lambda a: print(json.dumps(available_backends(), indent=2)) or 0)

    r = sub.add_parser("run", help="roda uma task com escolha adaptativa de modelo")
    r.add_argument("--task", required=True, choices=list(POLICIES))
    r.add_argument("--spec", required=True)
    r.add_argument("--context", action="append", default=[])
    r.add_argument("--max-lines", type=int, default=400)
    r.add_argument("--max-criteria", type=int, default=8)
    r.set_defaults(func=lambda a: print(json.dumps(
        run_task(a.task, Path(a.spec), a.context, a.max_lines, a.max_criteria),
        ensure_ascii=False, indent=2)) or 0)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
