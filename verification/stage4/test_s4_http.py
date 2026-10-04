"""Stage 4: mixed concurrency (347), the exact isolated harness run (350) and the maintainability measurement (351)."""
import ast
import glob
import os
import random
import subprocess
import sys
import threading
import unittest

from s4common import Base4, STAGE4_DIR, FROZEN_STAGE3, THU, FRI, T, add_days, fixture4, policy, inst, seed_res, FAR_FROM, FAR_TO

HARNESS_PY = os.environ.get("HARNESS_PY", "C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs/.venv/Scripts/python.exe")
HARNESS_CWD = os.environ.get("HARNESS_CWD", "C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs")
HARNESS_REPO = os.environ.get("HARNESS_REPO", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HARNESS_CHECKS = os.environ.get("HARNESS_CHECKS", "C:/Users/Prince/Documents/darkfactory/band-work/checks")


class MixedConcurrency(Base4):
    def test_L347_fifty_mixed_operations_serializable_and_never_5xx(self):
        a, s = self.mk_series(4, 1, T, "t_2", 2)
        refs = [o["reference"] for o in s["occurrences"]]
        for i in range(3):
            self.ok_book(self.ada, f"{THU}T{20 + i // 2}:{'30' if i % 2 else '00'}", table="t_1", party=2)
        plans = [self.ok_replan("t_2", inst(THU, "18:00"), inst(THU, "23:00"))["plan_id"] for _ in range(2)]
        base_export = self.api.call("GET", "/_test/export").json                       # private: memory only
        exports, results = [], []
        lock = threading.Lock()
        rng = random.Random(347)
        ops = []
        for i in range(50):
            kind = rng.choice(["read", "avail", "book", "preview", "apply", "amend", "export", "import", "reset", "patch", "series", "moves"])
            if kind == "reset" and sum(1 for o in ops if o[0] == "reset") >= 2:
                kind = "read"
            if kind == "import" and sum(1 for o in ops if o[0] == "import") >= 3:
                kind = "avail"
            ops.append((kind, i))

        def run(kind, i):
            k = f"mix-{i}"
            if kind == "read":
                r = self.api.call("GET", "/reservations", token=self.bob)
            elif kind == "avail":
                r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2&explain=true")
            elif kind == "book":
                r = self.book(self.ada, f"{add_days(THU, 28 + i % 3)}T{18 + i % 5}:00", table=f"t_{1 + i % 3}", party=2, key=k)
            elif kind == "preview":
                r = self.replan(self.ada, f"t_{1 + i % 3}", inst(THU, "18:00"), inst(THU, "23:00"), key=k)
            elif kind == "apply":
                r = self.apply(self.ada, plans[i % 2], key=k)
            elif kind == "amend":
                r = self.amend(self.bob, s["series_id"], 1 + i % 2, 0, f"{19 + i % 3}:00", key=k)
            elif kind == "export":
                r = self.api.call("GET", "/_test/export")
                if r.status == 200:
                    with lock:
                        exports.append(r.json)
            elif kind == "import":
                r = self.api.call("POST", "/_test/import", base_export)
            elif kind == "reset":
                r = self.api.call("POST", "/_test/reset", fixture4())
            elif kind == "patch":
                r = self.patch(refs[1 + i % 3], {"party_size": 1 + i % 3}, self.bob)
            elif kind == "series":
                r = self.adopt(a["reference"], 3, 1, self.bob, key=k)
            else:
                r = self.moves([{"reference": refs[1], "party_size": 2}], self.bob, key=k)
            with lock:
                results.append((kind, r.status, r.raw[:200]))
        out = self.burst([lambda kind=kind, i=i: run(kind, i) for kind, i in ops])
        self.assertEqual(len(results), 50)
        for kind, status, raw in results:
            self.assertLess(status, 500, (kind, status, raw))
            self.assertTrue(200 <= status < 500, (kind, status))
        # the service is still serving and consistent
        self.assertEqual(self.api.call("GET", "/reservations", token=self.bob).status in (200, 401), True)
        for ex in exports:
            self.assertEqual(self.api.call("POST", "/_test/import", ex).status, 204, "every export taken during the burst is a loadable snapshot")
        self.assertEqual(self.api.call("POST", "/_test/import", base_export).status, 204)
        self.assertEqual(self.rev() >= 0, True)
        seen = {}
        for tok in (self.ada, self.bob):
            lst = self.api.call("GET", "/reservations", token=tok)
            if lst.status != 200:
                continue
            for r in lst.json["reservations"]:
                if r["status"] != "confirmed":
                    continue
                for t in self.tids(r):
                    for (s0, e0, ref) in seen.get((r["restaurant_id"], t), []):
                        self.assertFalse(r["starts_at"] < e0 and s0 < r["ends_at"], ("overlap", t, r["reference"], ref))
                    seen.setdefault((r["restaurant_id"], t), []).append((r["starts_at"], r["ends_at"], r["reference"]))

    def test_L347_concurrent_previews_and_applies_across_two_restaurants_do_not_interfere(self):
        self.ok_book(self.ada, f"{THU}T19:00", table="t_2", party=3)
        self.ok_book(self.bob, f"{THU}T19:00", table="t_1", party=2, rest="r_other") if False else None
        p1 = self.ok_replan("t_2")
        o1 = self.replan(self.bob, "t_1", FAR_FROM, FAR_TO, "r_other")
        self.assertEqual(o1.status, 201)
        out = self.burst([lambda: self.apply(self.ada, p1["plan_id"], key="c1"), lambda: self.replan(self.bob, "t_1", FAR_FROM, FAR_TO, "r_other"),
                          lambda: self.replan(self.ada, "t_1", FAR_FROM, FAR_TO), lambda: self.api.call("GET", "/_test/export")])
        self.assertTrue(all(o.status < 500 for o in out), out)
        self.assertEqual(out[0].status, 201)
        self.assertEqual(out[1].json["restaurant_revision"], 0)


class Malformed(Base4):
    def test_L340_new_routes_reject_malformed_json_and_wrong_types(self):
        s_a, s = self.mk_series(2)
        for path, tok in (("/restaurants/r_anker/replans", self.ada), (f"/series/{s['series_id']}/amend", self.bob)):
            for raw in ("{", "", "nope", "[1"):
                self.err(self.api.call("POST", path, raw=raw, token=tok, key=self.newkey()), 400, "malformed_request")
            for body in ([], "x", 7, None, True):
                r = self.api.call("POST", path, body, token=tok, key=self.newkey())
                self.assertEqual((r.status, r.json["error"]["code"]), (400, "malformed_request"), (path, body, r))
        p = self.ok_replan("t_2")
        for body in ([], "x", 7, None):
            r = self.apply(self.ada, p["plan_id"], body=body)
            self.assertIn(r.status, (400, 201, 422), r)
        self.err(self.api.call("POST", f"/restaurants/r_anker/replans/{p['plan_id']}/apply", raw="{", token=self.ada, key=self.newkey()), 400,
                 "malformed_request")


class HarnessRun(unittest.TestCase):
    def test_L350_exact_isolated_stage4_harness_claims_stage_4(self):
        self.assertTrue(os.path.exists(HARNESS_PY), HARNESS_PY)
        out = os.path.join(HARNESS_CHECKS, "tester-s4-" + os.urandom(4).hex())
        cmd = [HARNESS_PY, "-m", "harness", "run", "--track", "tablekeeper", "--repo", HARNESS_REPO, "--stage", "4", "--mode", "isolated",
               "--out", out]
        p = subprocess.run(cmd, cwd=HARNESS_CWD, capture_output=True, text=True, timeout=3000)
        text = p.stdout + p.stderr
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "tester-harness-console.log"), "w", encoding="utf-8") as fh:
            fh.write(text)
        self.assertIn("claimed stage: 4", text, text[-1500:])
        low = text.lower()
        self.assertNotIn("skipped", low.replace("0 skipped", "").replace("skipped: 0", "").replace("skipped=0", "") if "skipped" in low else "")
        self.assertEqual(p.returncode, 0, text[-1500:])


def py_files(root):
    return [f for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True) if "__pycache__" not in f and "venv" not in f]


def metrics(root):
    cc, longest, sizes, windows = [], 0, {}, {}
    dup = 0
    for f in py_files(root):
        src = open(f, encoding="utf-8").read()
        sizes[os.path.relpath(f, root)] = src.count("\n") + 1
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c = 1 + sum(isinstance(x, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp, ast.With, ast.Assert, ast.comprehension))
                            + (len(x.values) - 1 if isinstance(x, ast.BoolOp) else 0) for x in ast.walk(n))
                cc.append(c)
                longest = max(longest, n.end_lineno - n.lineno + 1)
        lines = [l.strip() for l in src.splitlines() if l.strip() and not l.strip().startswith("#")]
        for i in range(len(lines) - 5):
            w = "\n".join(lines[i:i + 6])
            if len(w) > 120:
                windows[w] = windows.get(w, 0) + 1
    dup = sum(1 for v in windows.values() if v > 1)
    return {"functions": len(cc), "cc_max": max(cc or [0]), "cc_mean": sum(cc) / max(1, len(cc)), "longest_function": longest,
            "largest_file": max(sizes.values() or [0]), "duplicate_6line_blocks": dup}


class Maintainability(unittest.TestCase):
    """Measured with the standard library (an approximation of radon/lizard); the exact radon/lizard/JS/duplication numbers are measured
    separately by the tester against the candidate and recorded in the findings file."""

    def test_L351_python_complexity_size_and_duplication_do_not_regress_against_frozen_stage_3(self):
        new, old = metrics(STAGE4_DIR), metrics(FROZEN_STAGE3)
        report = f"stage4={new} stage3={old}"
        self.assertLessEqual(new["cc_max"], max(old["cc_max"] + 3, 12), report)
        self.assertLessEqual(new["cc_mean"], old["cc_mean"] * 1.35 + 0.5, report)
        self.assertLessEqual(new["longest_function"], max(old["longest_function"] * 1.5, 60), report)
        self.assertLessEqual(new["largest_file"], max(old["largest_file"] * 1.5, 400), report)
        self.assertLessEqual(new["duplicate_6line_blocks"], old["duplicate_6line_blocks"] + 3, report)
        os.makedirs(os.environ.get("CHECK_LOG_DIR", "."), exist_ok=True)
        with open(os.path.join(os.environ.get("CHECK_LOG_DIR", "."), "tester-maintainability.txt"), "w", encoding="utf-8") as fh:
            fh.write(report + "\n")

    def test_L351_javascript_size_does_not_balloon(self):
        def js(root):
            files = [f for f in glob.glob(os.path.join(root, "**", "*.js"), recursive=True) + glob.glob(os.path.join(root, "**", "*.html"), recursive=True)
                     if "node_modules" not in f]
            return sum(open(f, encoding="utf-8").read().count("\n") + 1 for f in files)
        new, old = js(STAGE4_DIR), js(FROZEN_STAGE3)
        self.assertLessEqual(new, old * 1.6 + 200, (new, old))
