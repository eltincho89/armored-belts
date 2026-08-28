"""Minimal zero-dependency test harness.

pytest is not installed in this environment and the suite has to stay runnable
from a bare `python`, so tests are plain functions registered with @test and
assertions are recorded rather than raised: one bad value reports one failure
instead of aborting the whole suite.
"""

import time
import traceback

REGISTRY = []


def test(suite, name):
    def deco(fn):
        REGISTRY.append((suite, name, fn))
        return fn
    return deco


class Tester:
    """Collects assertion results for a single test function."""

    def __init__(self, report):
        self._report = report
        self.checks = []

    def _record(self, ok, label, detail):
        self.checks.append((ok, label, detail))
        self._report.record(ok, label, detail)

    def true(self, cond, label, detail=""):
        self._record(bool(cond), label, detail or "condition was false")
        return bool(cond)

    def eq(self, actual, expected, label):
        return self._record(actual == expected, label,
                            "expected %r, got %r" % (expected, actual)) or actual == expected

    def near(self, actual, expected, tol, label):
        try:
            ok = abs(actual - expected) <= tol
        except TypeError:
            ok = False
        self._record(ok, label, "expected %r +/- %r, got %r" % (expected, tol, actual))
        return ok

    def is_none(self, actual, label):
        self._record(actual is None, label, "expected None, got %r" % (actual,))

    def contains(self, haystack, needle, label):
        self._record(needle in haystack, label, "%r not found" % (needle,))

    def empty(self, collection, label):
        items = list(collection)
        preview = ", ".join(str(i) for i in items[:8])
        if len(items) > 8:
            preview += ", ... (%d total)" % len(items)
        self._record(not items, label, "unexpected entries: " + preview)


class Report:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self._suite = None
        self._test = None

    def record(self, ok, label, detail):
        if ok:
            self.passed += 1
            if self.verbose:
                print("      ok   %s" % label)
        else:
            self.failures.append((self._suite, self._test, label, detail))
            print("      FAIL %s -- %s" % (label, detail))
        return ok

    def run(self, only=None):
        started = time.time()
        suite = None
        for suite_name, test_name, fn in REGISTRY:
            if only and only not in suite_name and only not in test_name:
                continue
            if suite_name != suite:
                suite = suite_name
                print("\n== %s ==" % suite)
            self._suite, self._test = suite_name, test_name
            before_fail = len(self.failures)
            print("   -- %s" % test_name)
            try:
                fn(Tester(self))
            except Skip as exc:
                self.skipped.append((suite_name, test_name, str(exc)))
                print("      SKIP %s" % exc)
            except Exception:
                self.errors.append((suite_name, test_name, traceback.format_exc()))
                print("      ERROR %s" % traceback.format_exc().strip().splitlines()[-1])
            else:
                if len(self.failures) == before_fail and not self.verbose:
                    print("      ok")
        self.elapsed = time.time() - started
        return self

    def summary(self):
        print("\n" + "=" * 68)
        print("passed: %d   failed: %d   errors: %d   skipped: %d   (%.1fs)"
              % (self.passed, len(self.failures), len(self.errors),
                 len(self.skipped), self.elapsed))
        if self.failures:
            print("\nFAILURES")
            for suite, test_name, label, detail in self.failures:
                print("  [%s] %s\n     %s\n     %s" % (suite, test_name, label, detail))
        if self.errors:
            print("\nERRORS")
            for suite, test_name, tb in self.errors:
                print("  [%s] %s\n%s" % (suite, test_name, tb))
        if self.skipped:
            print("\nSKIPPED")
            for suite, test_name, why in self.skipped:
                print("  [%s] %s -- %s" % (suite, test_name, why))
        ok = not self.failures and not self.errors
        print("\nRESULT: %s" % ("PASS" if ok else "FAIL"))
        print("=" * 68)
        return 0 if ok else 1


class Skip(Exception):
    """Raised by a test that cannot run in the current environment."""
