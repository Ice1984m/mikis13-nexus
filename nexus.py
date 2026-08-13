#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from nexuslib.core import (
    ROOT,
    analyze,
    architecture,
    full_test,
    performance_check,
    remember,
    safe_repair,
    security_scan
)

def out(data):
    print(json.dumps(data,indent=2,ensure_ascii=False))

def create(args):
    idea = " ".join(args).strip()

    if not idea:
        raise SystemExit('Gebruik: nexus create "idee"')

    plan = architecture(idea)

    path = ROOT/"reports"/f"architect-{plan['name']}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(plan,indent=2,ensure_ascii=False))

    out(plan)

def status():
    tests, _ = full_test()
    secrets = security_scan()

    out({
        "service": "mikis13-nexus",
        "tests": "PASS" if tests else "FAIL",
        "security": "PASS" if not secrets else "FAIL",
        "secret_hits": secrets,
        "performance": performance_check()
    })

def test():
    ok, results = full_test()
    out({"ok":ok,"results":results})
    raise SystemExit(0 if ok else 1)

def repair():
    actions = safe_repair()
    ok, results = full_test()

    out({
        "repair_actions": actions,
        "ok": ok,
        "results": results
    })

    raise SystemExit(0 if ok else 1)

def audit():
    secrets = security_scan()
    out({
        "security": "PASS" if not secrets else "FAIL",
        "secret_hits": secrets,
        "performance": performance_check()
    })
    raise SystemExit(0 if not secrets else 1)

def debug(args):
    problem = " ".join(args).strip()

    if not problem:
        raise SystemExit('Gebruik: nexus debug "probleem"')

    out(analyze(problem))

def learn(args):
    if len(args) < 2:
        raise SystemExit('Gebruik: nexus learn "probleem" PASS|FAIL')

    status = args[-1]
    problem = " ".join(args[:-1])

    out(remember(problem,status))

def evolve():
    from nexuslib.core import db

    with db() as conn:
        rows = conn.execute("""
        SELECT problem,pass_count,fail_count,solution
        FROM patterns
        ORDER BY pass_count DESC, fail_count DESC
        LIMIT 30
        """).fetchall()

    suggestions = []

    for problem, pc, fc, solution in rows:
        if pc > 0:
            suggestions.append({
                "problem": problem,
                "type": "KNOWN_GOOD",
                "passes": pc,
                "suggestion": solution or "Reuse verified pattern"
            })

        elif fc >= 3:
            suggestions.append({
                "problem": problem,
                "type": "ANTI_LOOP",
                "failures": fc,
                "suggestion": "Change strategy; do not repeat failed repair"
            })

    out({
        "mode": "proposal-only",
        "auto_modify_main": False,
        "suggestions": suggestions
    })

def selftest():
    p = architecture("Nexus Test Project")
    assert p["name"] == "nexus-test-project"

    r = remember("__nexus_selftest__", "FAIL")
    assert r["known"] is True

    print("SELFTEST PASS")

def main():
    if len(sys.argv) < 2:
        print("""
MIKIS13 NEXUS PRO

nexus create "idee"
nexus status
nexus test
nexus repair
nexus audit
nexus debug "probleem"
nexus learn "probleem" FAIL
nexus learn "probleem" PASS
nexus evolve
""")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "create": lambda: create(args),
        "status": status,
        "test": test,
        "repair": repair,
        "audit": audit,
        "debug": lambda: debug(args),
        "analyze": lambda: debug(args),
        "learn": lambda: learn(args),
        "evolve": evolve,
        "selftest": selftest
    }

    if cmd not in commands:
        raise SystemExit(f"Onbekend commando: {cmd}")

    commands[cmd]()

if __name__ == "__main__":
    main()
