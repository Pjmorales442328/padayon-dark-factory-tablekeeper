"""Stage 3 delivery, limits, process lines and 50-in-flight serializability (ledger 1-10, 112-117, 191, 195-197, 285, 291-292)."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unittest

import s3common
from s3common import (Api, Base3, REPO, STAGE3_DIR, FROZEN_STAGE1, FROZEN_STAGE2, THU, T, add_days, fixture3, policy, common)

REV1 = "344e085d8e3d0629dcc17fc95f22a43efe2a85d2"
REV2 = "94e7654c4427fa3c087279675edbe1cda4f5a4fc"
SEATS = {"coordinator", "core-builder", "interface-builder", "tester", "reviewer"}
KICKOFF = os.environ.get("KICKOFF", "C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs")


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True).stdout


class Delivery3(unittest.TestCase):
    def test_L001_L002_L117_stage3_folder_and_frozen_stages(self):
        for f in ("Dockerfile", "RUN.md", "requirements.txt"):
            self.assertTrue(os.path.isfile(os.path.join(STAGE3_DIR, f)), f)
        names = [n.lower() for _, d, fs in os.walk(STAGE3_DIR) for n in d + fs if "__pycache__" not in n]
        self.assertNotIn(".git", names)
        self.assertTrue(os.path.isdir(os.path.join(STAGE3_DIR, "tablekeeper")))
        for rev, d in ((REV1, "stage-1"), (REV2, "stage-2")):
            self.assertEqual(git("diff", "--stat", rev, "HEAD", "--", d).strip(), "", f"{d} changed since its frozen revision")
        self.assertEqual(git("ls-files", "stage-3").count("__pycache__"), 0, "generated caches must not be tracked")

    def test_L117_builder_notes_cover_all_292_ledger_lines(self):
        base = os.path.join(REPO, "handoffs")
        missing = {}
        for seat in ("core-builder", "interface-builder"):
            files = [f for f in os.listdir(base) if f.startswith(seat) and "stage-3" in f]
            self.assertTrue(files, f"no stage-3 notes for {seat}")
            nums = set()
            for f in files:
                nums |= {int(m) for m in re.findall(r"(?m)^\s*(?:[-*]\s*)?(?:\[[ xX]\]\s*)?(\d{1,3})\.", open(os.path.join(base, f), encoding="utf-8").read())}
            gone = [n for n in range(1, 293) if n not in nums]
            if gone:
                missing[seat] = gone[:20]
        self.assertEqual(missing, {})

    def test_L002_L003_runmd_and_dockerfile_for_stage3(self):
        run = open(os.path.join(STAGE3_DIR, "RUN.md"), encoding="utf-8").read()
        self.assertRegex(run, r"docker\s+build")
        self.assertRegex(run, r"docker\s+run")
        self.assertIn("PORT", run)
        self.assertRegex(run, r"stage-?3", "RUN.md must describe the stage-3 build path/tag")
        df = open(os.path.join(STAGE3_DIR, "Dockerfile"), encoding="utf-8").read()
        self.assertRegex(df, r"(?im)^FROM\s+\S*python")
        self.assertRegex(df, r"(?im)^(CMD|ENTRYPOINT)\b")
        self.assertNotRegex(run.lower(), r"docker[- ]compose")
        for svc in ("redis", "postgres", "mysql", "mongo", "rabbit", "kafka"):
            self.assertNotIn(svc, run.lower() + df.lower())

    def docker_ok(self):
        return subprocess.run(["docker", "info"], capture_output=True, timeout=60).returncode == 0

    def test_L003_L004_L005_L006_L007_docker_build_run_default_and_custom_port_no_network(self):
        if not self.docker_ok():
            self.fail("docker daemon not available: container requirements could not be observed")
        tag = "tk-stage3-check"
        b = subprocess.run(["docker", "build", "-t", tag, STAGE3_DIR], capture_output=True, text=True, timeout=1200)
        self.assertEqual(b.returncode, 0, b.stdout[-600:] + b.stderr[-600:])
        port = common.free_port()
        name = f"tk3-check-{port}"
        r = subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "--cpus", "2", "-m", "2g", "-e", "PORT=8099",
                            "-p", f"{port}:8099", tag], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        try:
            api = Api(f"http://127.0.0.1:{port}")
            t0 = time.time()
            ok = False
            while time.time() - t0 < 60:
                try:
                    if api.call("GET", "/health", timeout=2).status == 200:
                        ok = True
                        break
                except Exception:
                    time.sleep(0.5)
            self.assertTrue(ok, "no healthy response within 60 s")
            print(f"[measure] docker start to healthy {time.time() - t0:.1f}s", file=sys.stderr)
            self.assertEqual(api.call("POST", "/_test/reset", fixture3()).status, 204)
            for p in ("/", "/signup", "/login", "/lookup"):
                x = api.call("GET", p)
                self.assertEqual((x.status, x.ctype.startswith("text/html")), (200, True), p)
            ex = api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2&explain=true")
            self.assertEqual(ex.status, 200)
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        # default port 8080 (published), runtime without any network
        name = f"tk3-default-{port}"
        r = subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "--network", "none", "--cpus", "2", "-m", "2g", tag],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        try:
            probe = ("import urllib.request,sys;u='http://127.0.0.1:8080/';"
                     "sys.exit(0 if urllib.request.urlopen(u+'health',timeout=2).status==200 and "
                     "urllib.request.urlopen(u+'login',timeout=2).status==200 else 1)")
            code = 1
            for _ in range(120):
                code = subprocess.run(["docker", "exec", name, "python", "-c", probe], capture_output=True).returncode
                if code == 0:
                    break
                time.sleep(0.5)
            self.assertEqual(code, 0, "healthy on the default port 8080 and serving the UI with --network none")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)


class Process3(unittest.TestCase):
    def test_L112_kickoff_matches_manifest(self):
        man = json.load(open(os.path.join(KICKOFF, "kickoff-manifest.json"), encoding="utf-8"))
        diffs = []
        for rel, h in man.items():
            p = os.path.join(KICKOFF, rel)
            if not os.path.isfile(p):
                diffs.append(f"missing {rel}")
                continue
            raw = open(p, "rb").read()
            norm = raw.replace(bytes([13, 10]), bytes([10]))
            if h not in (hashlib.sha256(raw).hexdigest(), hashlib.sha256(norm).hexdigest()):
                diffs.append(f"modified {rel}")
        self.assertEqual(diffs, [])

    def test_L112_kickoff_untouched_since_run_started(self):
        first = int(git("log", "--reverse", "--format=%ct").split()[0])
        late = []
        for root, dirs, files in os.walk(KICKOFF):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", ".pytest_cache")]
            for n in files:
                p = os.path.join(root, n)
                if os.path.getmtime(p) > first:
                    late.append(os.path.relpath(p, KICKOFF))
        self.assertEqual(late, [])

    def test_L113_L195_every_ledger_line_has_a_check(self):
        import coverage_map3
        self.assertEqual(coverage_map3.missing_lines(), [])

    def test_L114_L195_harness_claimed_stage_3(self):
        out = os.environ.get("HARNESS_OUT")
        if not out:
            self.fail("HARNESS_OUT not set: point it at the stage 3 harness output folder or console log")
        txt = ""
        if os.path.isdir(out):
            for root, _, files in os.walk(out):
                for f in files:
                    if f.endswith((".txt", ".log", ".json", ".md")):
                        txt += open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        else:
            txt = open(out, encoding="utf-8", errors="replace").read()
        self.assertRegex(txt, r"claimed stage:\s*3\b")

    def test_L115_commit_authors(self):
        for r in git("log", "--format=%H|%an|%ae").strip().splitlines():
            h, an, ae = r.split("|")
            self.assertIn(an, SEATS, f"{h[:8]} author {an!r}")
            self.assertNotRegex(ae, r"@(gmail|outlook|yahoo|hotmail|icloud)\.", f"{h[:8]}")

    def test_L116_coordinator_does_not_edit_service_checks_or_frozen_stages(self):
        out = git("log", "--author=^coordinator$", "--name-only", "--format=", "--", "stage-1", "stage-2", "stage-3", "verification",
                  "README.md", "FACTORY.md").strip()
        self.assertEqual(out, "")

    def test_L191_browser_tooling_present_in_this_interpreter(self):
        import playwright  # noqa: F401
        import axe_playwright_python  # noqa: F401
        from playwright.sync_api import sync_playwright
        from browser_helpers import launch
        with sync_playwright() as p:
            b = launch(p)
            pg = b.new_page()
            pg.set_content("<p>ok</p>")
            self.assertEqual(pg.inner_text("p"), "ok")
            b.close()

    @staticmethod
    def metrics_python():
        import shutil
        for c in (os.environ.get("METRICS_PYTHON"), sys.executable, shutil.which("python"), "C:/Python314/python.exe"):
            if c and subprocess.run([c, "-c", "import radon"], capture_output=True).returncode == 0:
                return c
        return None

    def test_L196_maintainability_against_the_frozen_stage2_baseline(self):
        py = self.metrics_python()
        self.assertIsNotNone(py, "radon is not importable by any known interpreter (set METRICS_PYTHON)")
        res = {}
        for name, d in (("stage-2", FROZEN_STAGE2), ("stage-3", STAGE3_DIR)):
            pkg = os.path.join(d, "tablekeeper")
            cc = subprocess.run([py, "-m", "radon", "cc", "-a", "-s", "-j", pkg], capture_output=True, text=True)
            mi = subprocess.run([py, "-m", "radon", "mi", "-s", "-j", pkg], capture_output=True, text=True)
            self.assertEqual(cc.returncode, 0, cc.stderr[-300:])
            blocks = [b for v in json.loads(cc.stdout).values() if isinstance(v, list) for b in v]
            mis = json.loads(mi.stdout)
            lz = subprocess.run([sys.executable, "-m", "lizard", pkg, "-l", "python", "--csv"], capture_output=True, text=True)
            rows = [r.split(",") for r in lz.stdout.strip().splitlines()] if lz.returncode == 0 else []
            res[name] = {"max_cc": max(b["complexity"] for b in blocks), "mean_cc": sum(b["complexity"] for b in blocks) / len(blocks),
                         "min_mi": min(v["mi"] for v in mis.values()), "ranks": sorted({v["rank"] for v in mis.values()}),
                         "lizard_functions": len(rows), "lizard_max_ccn": max((int(r[1]) for r in rows), default=None),
                         "lizard_nloc": sum(int(r[0]) for r in rows) if rows else None}
        print("[measure] maintainability", json.dumps(res), file=sys.stderr)
        s3 = res["stage-3"]
        self.assertLessEqual(s3["max_cc"], 20, "a function is too complex")
        self.assertEqual(s3["ranks"], ["A"], "every stage-3 file needs maintainability rank A")
        self.assertLessEqual(s3["mean_cc"], res["stage-2"]["mean_cc"] * 1.5 + 0.5, "mean complexity regressed against stage 2")

    def test_L292_final_report_record_exists(self):
        rec = open(os.path.join(REPO, "handoffs", "stage-3-record.md"), encoding="utf-8").read().lower()
        for needle in ("stage 3", "claimed stage: 3"):
            self.assertIn(needle, rec)


class Concurrency3(Base3):
    def test_L285_L180_fifty_in_flight_mixed_new_paths_stay_serializable(self):
        bob, ada = self.bob, self.ada
        refs = [self.ok_book(bob, f"{THU}T{h}:00", table=t, party=1)["reference"] for h, t in (("18", "t_1"), ("19", "t_2"), ("20", "t_3"))]
        anchor = self.ok_book(bob, f"{add_days(THU, 70)}T19:00", table="t_2", party=2)
        calls = []
        for i in range(60):
            k = i % 6
            if k == 0:
                calls.append(lambda i=i: self.publish(ada, policy(add_days("2030-06-01", i)), key=f"mix-p{i}"))
            elif k == 1:
                calls.append(lambda i=i: self.patch(refs[i % 3], {"party_size": 1 + i % 2}, bob))
            elif k == 2:
                calls.append(lambda i=i: self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2&explain=true"))
            elif k == 3:
                calls.append(lambda i=i: self.api.call("GET", f"/reservations/{refs[i % 3]}/history", token=bob))
            elif k == 4:
                calls.append(lambda i=i: self.adopt(anchor["reference"], 3, 1, bob, key=f"mix-s{i}"))
            else:
                calls.append(lambda i=i: self.api.call("GET", f"/reservations/{refs[i % 3]}/decision", token=bob))
        t0 = time.time()
        outs = self.burst(calls[:50]) + self.burst(calls[50:])
        print(f"[measure] 60 mixed new-path requests {time.time() - t0:.2f}s", file=sys.stderr)
        self.assertTrue(all(o.status < 500 for o in outs), [o.status for o in outs if o.status >= 500][:5])
        pubs = [o for o in outs if o.status == 201 and "policy_version" in (o.json or {})]
        self.assertEqual(sorted(o.json["policy_version"] for o in pubs), list(range(1, len(pubs) + 1)))
        adoptions = [o for o in outs if o.status == 201 and "series_id" in (o.json or {})]
        self.assertEqual(len(adoptions), 1, "exactly one adoption of the shared anchor")
        for o in outs:
            if o.status == 409 and "error" in (o.json or {}):
                self.assertEqual(o.json["error"]["code"], "already_in_series")
        for ref in refs:
            ents = self.history(ref, bob)["entries"]
            self.assertEqual([e["revision"] for e in ents], list(range(1, len(ents) + 1)))
            self.assertEqual(self.get_res(ref, bob)["revision"], len(ents))
        s = adoptions[0].json
        g = self.get_series(s["series_id"], bob)
        self.assertEqual(len(g["occurrences"]), 3)
        self.assertEqual(self.api.call("GET", "/health").status, 200)
