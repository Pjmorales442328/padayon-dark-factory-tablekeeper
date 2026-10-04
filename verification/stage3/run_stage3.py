"""Run the stage 3 independent checks with the harness interpreter.

  <harness python> verification/stage3/run_stage3.py --out <folder outside the repo> [-k text] [--part inherited1|inherited2|api|browser|all]

Runs (1) the frozen stage-1 checks, (2) the frozen stage-2 checks and (3) the stage-3 checks, all against the stage-3 service.
Inherited assertions whose exact expectation was changed by a stage-3 requirement are listed in SUPERSEDED (visible in the
report, never skipped) and each has a replacement stage-3 check.
Env: HARNESS_OUT, SHOT_DIR, S3_DIR (service folder), FROZEN_STAGE1/FROZEN_STAGE2, BASE_URL/BASE_URL2, SERVICE_CMD, KICKOFF.
"""
import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s3common  # noqa: E402,F401  (must come first: points the frozen helpers at stage-3)

SUPERSEDED = {
    "test_b_booking.Availability.test_L057_L058_L059_shape_and_grid":
        "frozen stage-1 strict slot key set (stage 2 added available_options); replaced by stage-3 test_s3_explain_policy.Explain.test_L200_*",
    "test_b_booking.Create.test_L062_shape":
        "frozen stage-1 strict reservation key set (stage 2/3 added table_ids, revision, accepted_terms); replaced by test_s3_booking_history.Terms.test_L062_L230_*",
    "test_s2_api.Create.test_L062_L166_shapes":
        "frozen stage-2 strict reservation key set (stage 3 adds revision and accepted_terms); replaced by test_s3_booking_history.Terms.test_L062_L230_*",
    "test_s2_transfer.TestUpgrade.test_L154_L184_references_resolve_and_singletons_gain_table_ids":
        "frozen stage-2 expectation that imported bookings equal the source plus table_ids only (stage 3 adds revision 1 and policy-0 terms); replaced by test_s3_transfer.UpgradeBase.test_L261_L282_*",
}


def collect(part):
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    if part in ("inherited1", "all"):
        for m in ("test_a_basics", "test_b_booking", "test_c_idempotency_moves", "test_d_dst", "test_e_transfer"):
            suite.addTests(loader.loadTestsFromName(m))
        import test_f_process
        for c in (test_f_process.Runtime, test_f_process.Load):
            suite.addTests(loader.loadTestsFromTestCase(c))
    if part in ("inherited2", "all"):
        for m in ("test_s2_api", "test_s2_transfer"):
            suite.addTests(loader.loadTestsFromName(m))
        import test_s2_http
        suite.addTests(loader.loadTestsFromTestCase(test_s2_http.Html))
        for m in ("test_s2_browser", "test_s2_visual", "test_s2_upgrade_browser"):
            suite.addTests(loader.loadTestsFromName(m))
    if part in ("api", "all"):
        for m in ("test_s3_explain_policy", "test_s3_booking_history", "test_s3_series_moves", "test_s3_transfer", "test_s3_http"):
            suite.addTests(loader.loadTestsFromName(m))
    if part in ("browser", "all"):
        for m in ("test_s3_browser", "test_s3_upgrade_browser"):
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
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "tk_stage3"))
    ap.add_argument("-k", dest="pattern")
    ap.add_argument("--part", default="all", choices=["all", "inherited1", "inherited2", "api", "browser"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.environ["CHECK_LOG_DIR"] = a.out
    os.environ.setdefault("SHOT_DIR", os.path.join(a.out, "screenshots"))
    os.makedirs(os.environ["SHOT_DIR"], exist_ok=True)
    tests = list(flatten(collect(a.part)))
    if a.pattern:
        tests = [t for t in tests if a.pattern in t.id()]
    with open(os.path.join(a.out, "stage3-checks.log"), "w", encoding="utf-8") as fh:
        res = unittest.TextTestRunner(stream=fh, verbosity=2).run(unittest.TestSuite(tests))
    bad = res.failures + res.errors
    sup = [(t, tb) for t, tb in bad if t.id() in SUPERSEDED]
    real = [(t, tb) for t, tb in bad if t.id() not in SUPERSEDED]
    print(f"ran {res.testsRun}, failed {len(res.failures)}, errors {len(res.errors)}, skipped {len(res.skipped)}, superseded-by-stage-3 {len(sup)}")
    for t, tb in real:
        print("FAIL", t.id(), "|", tb.strip().splitlines()[-1][:300])
    for t, tb in sup:
        print("SUPERSEDED", t.id(), "|", SUPERSEDED[t.id()])
    for t, why in res.skipped:
        print("SKIP", t.id(), "|", why)
    sys.exit(1 if real else 0)


if __name__ == "__main__":
    main()
