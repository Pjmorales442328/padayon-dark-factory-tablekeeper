"""Stage 2 HTML routes, static assets, delivery, resources and process lines (ledger 1-10, 112-118, 191, 195-197)."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unittest
import urllib.parse

import s2common
from s2common import Api, Base2, REPO, STAGE1_DIR, STAGE2_DIR, THU, fixture2, base_url, common, start_service

FROZEN_REV = "344e085d8e3d0629dcc17fc95f22a43efe2a85d2"
SEATS = {"coordinator", "core-builder", "interface-builder", "tester", "reviewer"}
KICKOFF = os.environ.get("KICKOFF", "C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs")
SCREENS = {"/": ["restaurant-select", "date-input", "party-size-input", "search-button"],
           "/signup": ["signup-email", "signup-password", "signup-display-name", "signup-submit"],
           "/login": ["login-email", "login-password", "login-submit"],
           "/lookup": ["lookup-reference-input", "lookup-submit"]}


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True).stdout


class Html(Base2):
    def test_L118_screen_routes_return_html(self):
        for path, ids in SCREENS.items():
            r = self.api.call("GET", path, headers={"Accept": "text/html"})
            self.assertEqual(r.status, 200, path)
            self.assertTrue(r.ctype.lower().startswith("text/html"), (path, r.ctype))
            body = r.raw.decode("utf-8", "replace")
            self.assertRegex(body.lower(), r"<!doctype html|<html")
            self.assertRegex(body, r"<title>\s*\S")
            if os.environ.get("S2_SSR_IDS", "0") == "1":
                for i in ids:
                    self.assertIn(i, body)

    def test_L118_api_still_json(self):
        for p in ("/restaurants", "/restaurants/zzz", "/health", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2"):
            r = self.api.call("GET", p, headers={"Accept": "text/html"})
            self.assertTrue(r.ctype.lower().replace(" ", "").startswith("application/json;charset=utf-8"), (p, r.ctype))
        r = self.api.call("GET", "/definitely/not/here")
        self.assertEqual(r.status, 404)
        self.assertLess(self.api.call("GET", "/signup/", headers={}).status, 500)
        r = self.api.call("POST", "/", {"x": 1})
        self.assertLess(r.status, 500)

    def test_L011_L032_api_errors_unaffected_by_ui_routes(self):
        r = self.api.call("GET", "/reservations")
        self.err(r, 401, "unauthenticated")
        r = self.api.call("GET", "/reservations/NOPE12", token=self.ada)
        self.err(r, 404, "not_found")

    def assets(self, path):
        body = self.api.call("GET", path).raw.decode("utf-8", "replace")
        urls = re.findall(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', body) + re.findall(r'url\(\s*["\']?([^)"\']+)', body)
        urls += re.findall(r'@import\s+["\']([^"\']+)', body)
        return body, urls

    def test_L005_L118_assets_are_local_with_correct_mime(self):
        checked = 0
        for path in SCREENS:
            body, urls = self.assets(path)
            for u in urls:
                if u.startswith(("#", "mailto:", "data:", "javascript:")):
                    continue
                p = urllib.parse.urlparse(u)
                self.assertFalse(p.scheme in ("http", "https") and p.hostname not in ("127.0.0.1", "localhost"),
                                 f"external reference {u} on {path}")
                if p.path in SCREENS or p.path in ("", "/"):
                    continue
                full = urllib.parse.urljoin(path if path.endswith("/") else "/", p.path)
                r = self.api.call("GET", full)
                self.assertEqual(r.status, 200, (path, u))
                ct = r.ctype.lower()
                if full.endswith(".js") or full.endswith(".mjs"):
                    self.assertRegex(ct, r"(text|application)/(x-)?javascript", (full, ct))
                elif full.endswith(".css"):
                    self.assertTrue(ct.startswith("text/css"), (full, ct))
                elif full.endswith(".svg"):
                    self.assertTrue(ct.startswith("image/svg+xml"), (full, ct))
                elif full.endswith((".woff2", ".woff", ".ttf")):
                    self.assertTrue(ct.startswith(("font/", "application/font", "application/x-font")), (full, ct))
                elif full.endswith(".png"):
                    self.assertTrue(ct.startswith("image/png"), (full, ct))
                self.assertGreater(len(r.raw), 0)
                if full.endswith((".js", ".css")):
                    txt = r.raw.decode("utf-8", "replace")
                    ext = [m for m in re.findall(r"https?://[^\s\"')]+", txt) if "w3.org" not in m and "127.0.0.1" not in m
                           and "localhost" not in m]
                    self.assertEqual(ext, [], f"external URL in {full}")
                checked += 1
        self.assertGreater(checked, 0, "no local script/style assets found: UI must be self-contained")

    def test_L118_unknown_ui_paths_do_not_5xx(self):
        for p in ("/login/", "/lookup?reference=ABC", "/static/", "/static/../x", "/%2e%2e/etc", "/signup?x=1", "//"):
            self.assertLess(self.api.call("GET", p).status, 500, p)


class Delivery(unittest.TestCase):
    def test_L001_L002_L117_stage2_folder_and_frozen_stage1(self):
        for f in ("Dockerfile", "RUN.md", "requirements.txt"):
            self.assertTrue(os.path.isfile(os.path.join(STAGE2_DIR, f)), f)
        names = [n.lower() for _, d, fs in os.walk(STAGE2_DIR) for n in d + fs]
        self.assertNotIn(".git", names)
        self.assertTrue(os.path.isdir(os.path.join(STAGE2_DIR, "tablekeeper")))
        # stage-1 tree identical to the frozen revision
        diff = git("diff", "--stat", FROZEN_REV, "HEAD", "--", "stage-1").strip()
        self.assertEqual(diff, "", "stage-1 changed since the frozen revision")
        self.assertEqual(git("status", "--porcelain", "--", "stage-1").replace("?? stage-1/tablekeeper/__pycache__/", "").strip(), "")

    def test_L117_builder_restructuring_notes_cover_all_ledger_lines(self):
        base = os.path.join(REPO, "handoffs")
        missing = {}
        for seat in ("core-builder", "interface-builder"):
            files = [f for f in os.listdir(base) if f.startswith(seat) and "stage-2" in f]
            self.assertTrue(files, f"no stage-2 notes for {seat}")
            nums = set()
            for f in files:
                nums |= {int(m) for m in re.findall(r"(?m)^\s*(\d{1,3})\.", open(os.path.join(base, f), encoding="utf-8").read())}
            gone = [n for n in range(1, 198) if n not in nums]
            if gone:
                missing[seat] = gone[:20]
        self.assertEqual(missing, {})

    def test_L002_L003_runmd_and_dockerfile(self):
        run = open(os.path.join(STAGE2_DIR, "RUN.md"), encoding="utf-8").read()
        self.assertRegex(run, r"docker\s+build")
        self.assertRegex(run, r"docker\s+run")
        self.assertIn("PORT", run)
        df = open(os.path.join(STAGE2_DIR, "Dockerfile"), encoding="utf-8").read()
        self.assertRegex(df, r"(?im)^FROM\s+\S*python")
        self.assertRegex(df, r"(?im)^(CMD|ENTRYPOINT)\b")
        self.assertNotRegex(run.lower(), r"docker[- ]compose")
        for svc in ("redis", "postgres", "mysql", "mongo", "rabbit", "kafka"):
            self.assertNotIn(svc, run.lower() + df.lower())

    def docker_ok(self):
        return subprocess.run(["docker", "info"], capture_output=True, timeout=60).returncode == 0

    def test_L003_L004_L005_L006_L007_docker_build_and_run_without_network(self):
        if not self.docker_ok():
            self.fail("docker daemon not available: container requirements could not be observed")
        tag = "tk-stage2-check"
        b = subprocess.run(["docker", "build", "-t", tag, STAGE2_DIR], capture_output=True, text=True, timeout=1200)
        self.assertEqual(b.returncode, 0, b.stdout[-600:] + b.stderr[-600:])
        port = common.free_port()
        name = f"tk2-check-{port}"
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
            self.assertEqual(api.call("POST", "/_test/reset", fixture2()).status, 204)
            for p in ("/", "/signup", "/login", "/lookup"):
                x = api.call("GET", p)
                self.assertEqual(x.status, 200, p)
                self.assertTrue(x.ctype.startswith("text/html"), p)
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        # runtime without any network
        name = f"tk2-nonet-{port}"
        r = subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "--network", "none", "--cpus", "2", "-m", "2g",
                            "-e", "PORT=8099", tag], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        try:
            probe = ("import urllib.request,sys;u='http://127.0.0.1:8099/';"
                     "sys.exit(0 if urllib.request.urlopen(u+'health',timeout=2).status==200 and "
                     "urllib.request.urlopen(u+'login',timeout=2).status==200 else 1)")
            code = 1
            for _ in range(120):
                code = subprocess.run(["docker", "exec", name, "python", "-c", probe], capture_output=True).returncode
                if code == 0:
                    break
                time.sleep(0.5)
            self.assertEqual(code, 0, "healthy and serving UI with --network none")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)


class Process(unittest.TestCase):
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
        import coverage_map2
        self.assertEqual(coverage_map2.missing_lines(), [])

    def test_L114_L195_harness_claimed_stage_2(self):
        out = os.environ.get("HARNESS_OUT")
        if not out:
            self.fail("HARNESS_OUT not set: point it at the stage 2 harness output folder or console log")
        txt = ""
        if os.path.isdir(out):
            for root, _, files in os.walk(out):
                for f in files:
                    if f.endswith((".txt", ".log", ".json", ".md")):
                        txt += open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        else:
            txt = open(out, encoding="utf-8", errors="replace").read()
        self.assertRegex(txt, r"claimed stage:\s*2\b")

    def test_L115_commit_authors(self):
        for r in git("log", "--format=%H|%an|%ae").strip().splitlines():
            h, an, ae = r.split("|")
            self.assertIn(an, SEATS, f"{h[:8]} author {an!r}")
            self.assertNotRegex(ae, r"@(gmail|outlook|yahoo|hotmail|icloud)\.", f"{h[:8]}")

    def test_L116_coordinator_does_not_edit_service_checks_or_frozen_stage1(self):
        out = git("log", "--author=^coordinator$", "--name-only", "--format=", "--", "stage-1", "stage-2", "verification",
                  "README.md", "FACTORY.md").strip()
        self.assertEqual(out, "")

    def test_L191_browser_tooling_present_in_this_interpreter(self):
        import playwright  # noqa: F401
        import axe_playwright_python  # noqa: F401
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            from browser_helpers import launch
            b = launch(p)
            pg = b.new_page()
            pg.set_content("<p>ok</p>")
            self.assertEqual(pg.inner_text("p"), "ok")
            b.close()

    def test_L196_maintainability_measured_against_stage1(self):
        res = {}
        for name, d in (("stage-1", STAGE1_DIR), ("stage-2", STAGE2_DIR)):
            pkg = os.path.join(d, "tablekeeper")
            cc = subprocess.run(["python", "-m", "radon", "cc", "-a", "-s", "-j", pkg], capture_output=True, text=True)
            mi = subprocess.run(["python", "-m", "radon", "mi", "-s", "-j", pkg], capture_output=True, text=True)
            self.assertEqual(cc.returncode, 0, cc.stderr[-300:])
            blocks = [b for v in json.loads(cc.stdout).values() if isinstance(v, list) for b in v]
            mis = {k: v for k, v in json.loads(mi.stdout).items()}
            res[name] = {"max_cc": max(b["complexity"] for b in blocks), "mean_cc": sum(b["complexity"] for b in blocks) / len(blocks),
                         "min_mi": min(v["mi"] for v in mis.values()), "ranks": sorted({v["rank"] for v in mis.values()})}
        print("[measure] maintainability", json.dumps(res), file=sys.stderr)
        s2 = res["stage-2"]
        self.assertLessEqual(s2["max_cc"], 20, "a function is too complex")
        self.assertEqual(s2["ranks"], ["A"], "every stage-2 file needs maintainability rank A")
        self.assertLessEqual(s2["mean_cc"], res["stage-1"]["mean_cc"] * 1.5 + 0.5, "mean complexity regressed against stage 1")

    def test_L197_final_report_record_exists(self):
        rec = open(os.path.join(REPO, "handoffs", "stage-record.md"), encoding="utf-8").read().lower()
        for needle in ("stage 2", "claimed stage: 2"):
            self.assertIn(needle, rec)
