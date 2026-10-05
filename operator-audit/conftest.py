"""Operator audit: an independent, spec-derived suite run against the frozen stage images."""
import os, pathlib, sys
KICKOFF = pathlib.Path(os.environ.get("KICKOFF", "C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs"))  # the organisers' kickoff package: harness plugin and fixtures
sys.path[:0] = [str(KICKOFF), str(KICKOFF / "tablekeeper" / "test"), str(pathlib.Path(__file__).parent / "tests")]
import pytest

@pytest.fixture(scope="session")
def browser(base_url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        yield b
        b.close()
