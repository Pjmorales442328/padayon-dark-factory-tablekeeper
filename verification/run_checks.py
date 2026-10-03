"""Run the independent black-box checks.

  python verification/run_checks.py [--out DIR] [-k PATTERN]

Env: BASE_URL / BASE_URL2 (running services, second is the import target), SERVICE_CMD, SERVICE_CWD,
HARNESS_OUT (harness output folder for ledger 114), KICKOFF. Without BASE_URL the runner starts services itself
(`python -m tablekeeper.server` in stage-1, PORT chosen). Logs go to --out (keep it outside the repository).
"""
import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "tk_checks"))
    ap.add_argument("-k", dest="pattern")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.environ["CHECK_LOG_DIR"] = a.out
    suite = unittest.defaultTestLoader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
    if a.pattern:
        def flt(s):
            for t in s:
                if isinstance(t, unittest.TestSuite):
                    yield from flt(t)
                elif a.pattern in t.id():
                    yield t
        suite = unittest.TestSuite(flt(suite))
    with open(os.path.join(a.out, "checks.log"), "w", encoding="utf-8") as fh:
        res = unittest.TextTestRunner(stream=fh, verbosity=2).run(suite)
    bad = [(t.id(), tb.strip().splitlines()[-1][:300]) for t, tb in res.failures + res.errors]
    print(f"ran {res.testsRun}, failed {len(res.failures)}, errors {len(res.errors)}, skipped {len(res.skipped)}")
    for i, m in bad:
        print("FAIL", i.split('.', 1)[-1], "|", m)
    for t, why in res.skipped:
        print("SKIP", t.id().split('.', 1)[-1], "|", why)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
