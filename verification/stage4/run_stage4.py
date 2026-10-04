"""Run the stage 4 independent checks with the harness interpreter.

  <harness python> verification/stage4/run_stage4.py --out <folder outside the repo> [-k text]
        [--part inherited1|inherited2|inherited3|api|browser|harness|all]

Runs the frozen stage-1, stage-2 and stage-3 checks and the stage-4 checks, all against the stage-4 service. Inherited
assertions whose exact expectation was changed by a stage-4 requirement are listed in SUPERSEDED (visible in the report,
never skipped) and each has a replacement stage-4 check. Part `harness` (L350) runs the exact isolated harness command and
is excluded from `all` because it is slow; run it explicitly.
Env: HARNESS_OUT, SHOT_DIR, S4_DIR (service folder), FROZEN_STAGE1/2/3, BASE_URL/BASE_URL2, SERVICE_CMD, REPO.
"""
import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s4common  # noqa: E402,F401  (must come first: points the frozen helpers at stage-4)

SUPERSEDED = {
    "test_b_booking.Availability.test_L057_L058_L059_shape_and_grid":
        "frozen stage-1 strict slot key set (stage 2 added available_options); replaced by stage-3 test_s3_explain_policy.Explain.test_L200_*",
    "test_b_booking.Create.test_L062_shape":
        "frozen stage-1 strict reservation key set; replaced by test_s3_booking_history.Terms.test_L062_L230_*",
    "test_b_booking.Cancel.test_L075_cancel_frees":
        "frozen stage-1 cancel equality (stage 3 revision bump); replaced by test_s3_booking_history.Amend.test_L075_L076_L234_*",
    "test_s2_api.Create.test_L062_L166_shapes":
        "frozen stage-2 strict reservation key set; replaced by test_s3_booking_history.Terms.test_L062_L230_*",
    "test_s2_transfer.TestUpgrade.test_L154_L184_references_resolve_and_singletons_gain_table_ids":
        "frozen stage-2 import equality (stage 3 adds revision/terms); replaced by test_s3_transfer.UpgradeBase.test_L261_L282_*",
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
    if part in ("inherited3", "all"):
        for m in ("test_s3_explain_policy", "test_s3_booking_history", "test_s3_series_moves", "test_s3_transfer", "test_s3_http",
                  "test_s3_browser", "test_s3_upgrade_browser"):
            suite.addTests(loader.loadTestsFromName(m))
    if part in ("api", "all"):
        for m in ("test_s4_replan", "test_s4_series_amend", "test_s4_transfer"):
            suite.addTests(loader.loadTestsFromName(m))
        import test_s4_http
        for c in (test_s4_http.MixedConcurrency, test_s4_http.Malformed, test_s4_http.Maintainability):
            suite.addTests(loader.loadTestsFromTestCase(c))
    if part in ("browser", "all"):
        for m in ("test_s4_browser", "test_s4_upgrade_browser"):
            suite.addTests(loader.loadTestsFromName(m))
    if part == "harness":
        import test_s4_http
        suite.addTests(loader.loadTestsFromTestCase(test_s4_http.HarnessRun))
    return suite


def flatten(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            yield from flatten(t)
        else:
            yield t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "tk_stage4"))
    ap.add_argument("-k", dest="pattern")
    ap.add_argument("--part", default="all", choices=["all", "inherited1", "inherited2", "inherited3", "api", "browser", "harness"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.environ["CHECK_LOG_DIR"] = a.out
    os.environ.setdefault("SHOT_DIR", os.path.join(a.out, "screenshots"))
    os.makedirs(os.environ["SHOT_DIR"], exist_ok=True)
    tests = list(flatten(collect(a.part)))
    if a.pattern:
        tests = [t for t in tests if a.pattern in t.id()]
    with open(os.path.join(a.out, "stage4-checks.log"), "w", encoding="utf-8") as fh:
        res = unittest.TextTestRunner(stream=fh, verbosity=2).run(unittest.TestSuite(tests))
    bad = res.failures + res.errors
    sup = [(t, tb) for t, tb in bad if t.id() in SUPERSEDED]
    real = [(t, tb) for t, tb in bad if t.id() not in SUPERSEDED]
    print(f"ran {res.testsRun}, failed {len(res.failures)}, errors {len(res.errors)}, skipped {len(res.skipped)}, superseded-by-stage-4 {len(sup)}")
    for t, tb in real:
        print("FAIL", t.id(), "|", tb.strip().splitlines()[-1][:300])
    for t, tb in sup:
        print("SUPERSEDED", t.id(), "|", SUPERSEDED[t.id()])
    for t, why in res.skipped:
        print("SKIP", t.id(), "|", why)
    sys.exit(1 if real else 0)


if __name__ == "__main__":
    main()
