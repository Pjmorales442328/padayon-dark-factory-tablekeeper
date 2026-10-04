"""Which stage 3 ledger lines (1..292) have at least one check? Counts the frozen stage-1 and stage-2 checks that run against
stage 3 (inherited lines) plus verification/stage3 checks. Test names carry L### tokens.   Usage: python coverage_map3.py [-v]"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
LINES = range(1, 293)


def covered():
    cov = {}
    files = glob.glob(os.path.join(V1, "test_*.py")) + glob.glob(os.path.join(V1, "stage2", "test_*.py")) + glob.glob(os.path.join(HERE, "test_*.py"))
    for f in sorted(files):
        for ln in open(f, encoding="utf-8"):
            m = re.match(r"\s*def (test_\w+)", ln)
            if m:
                for n in re.findall(r"L(\d{3})", m.group(1)):
                    cov.setdefault(int(n), []).append(os.path.basename(f) + "::" + m.group(1))
    return cov


def missing_lines():
    c = covered()
    return [n for n in LINES if n not in c]


if __name__ == "__main__":
    c = covered()
    miss = missing_lines()
    print(f"ledger lines covered: {len(LINES) - len(miss)}/{len(LINES)}; checks: {sum(len(v) for v in c.values())}")
    if "-v" in sys.argv:
        for n in LINES:
            print(n, len(c.get(n, [])), ", ".join(x.split('::')[1] for x in c.get(n, [])[:2]))
    if miss:
        print("UNCOVERED:", miss)
        sys.exit(1)
