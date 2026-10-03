"""Run the stage 2 independent checks with the harness interpreter.

  <harness python> verification/stage2/run_stage2.py --out <folder outside the repo> [-k text] [--part inherited|api|browser|all]

Runs (1) the frozen stage-1 checks against stage-2 (inherited behaviour; their ids are listed in SUPERSEDED only where a
stage-2 requirement changed the asserted shape, each with a replacement stage-2 check), and (2) the stage-2 checks.
Env: HARNESS_OUT (stage 2 harness output for ledger 114), SHOT_DIR (screenshots), BASE_URL/BASE_URL2 (optional running
stage-2 services), SERVICE_CMD, KICKOFF.
"""
import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s2common  # noqa: E402,F401  (must come first: points the frozen helpers at stage-2)

V1 = os.path.dirname(HERE)

# frozen stage-1 assertions whose exact expectation changed by a stage-2 requirement -> replaced by named stage-2 checks
SUPERSEDED = {
    "test_b_booking.Availability.test_L057_L058_L059_shape_and_grid":
        "slots gain available_options (strict key-set in the frozen check); replaced by test_s2_api.Options.test_L058_L161_L162_*",
    "test_b_booking.Create.test_L062_shape":
        "responses carry table_ids (strict key-set in the frozen check); replaced by test_s2_api.Create.test_L062_L166_shapes",
}


def collect(part):
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    if part in ("inherited", "all"):
        for m in ("test_a_basics", "test_b_booking", "test_c_idempotency_moves", "test_d_dst", "test_e_transfer"):
            suite.addTests(loader.loadTestsFromName(m))
        import test_f_process
        for c in (test_f_process.Runtime, test_f_process.Load):
            suite.addTests(loader.loadTestsFromTestCase(c))
    names = {"api": ["test_s2_api", "test_s2_transfer", "test_s2_http"],
             "browser": ["test_s2_browser", "test_s2_visual", "test_s2_upgrade_browser"]}
    for grp in ("api", "browser"):
        if part in (grp, "all"):
            for m in names[grp]:
                suite.addTests(loader.loadTestsFromName(m))
    return suite


def flatten(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            yield from flatten(t)
        else:
            yield t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "tk_stage2"))
    ap.add_argument("-k", dest="pattern")
    ap.add_argument("--part", default="all", choices=["all", "inherited", "api", "browser"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.environ["CHECK_LOG_DIR"] = a.out
    os.environ.setdefault("SHOT_DIR", os.path.join(a.out, "screenshots"))
    os.makedirs(os.environ["SHOT_DIR"], exist_ok=True)
    tests = list(flatten(collect(a.part)))
    if a.pattern:
        tests = [t for t in tests if a.pattern in t.id()]
    suite = unittest.TestSuite(tests)
    with open(os.path.join(a.out, "stage2-checks.log"), "w", encoding="utf-8") as fh:
        res = unittest.TextTestRunner(stream=fh, verbosity=2).run(suite)
    bad = res.failures + res.errors
    sup = [(t, tb) for t, tb in bad if t.id() in SUPERSEDED]
    real = [(t, tb) for t, tb in bad if t.id() not in SUPERSEDED]
    print(f"ran {res.testsRun}, failed {len(res.failures)}, errors {len(res.errors)}, skipped {len(res.skipped)}, "
          f"superseded-by-stage-2 {len(sup)}")
    for t, tb in real:
        print("FAIL", t.id(), "|", tb.strip().splitlines()[-1][:300])
    for t, tb in sup:
        print("SUPERSEDED", t.id(), "|", SUPERSEDED[t.id()])
    for t, why in res.skipped:
        print("SKIP", t.id(), "|", why)
    sys.exit(1 if real else 0)


if __name__ == "__main__":
    main()
