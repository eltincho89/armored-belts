"""Test runner for the armored-belts mod.

    python tools/run_tests.py            # run every test against the current dump
    python tools/run_tests.py --dump     # regenerate the dump first, then run
    python tools/run_tests.py -k balance # run one suite
    python tools/run_tests.py -v         # list every individual assertion

--dump launches `factorio.exe --dump-data`, which boots the game, builds every
prototype of every enabled mod, writes script-output/data-raw-dump.json and
exits. It is the real data stage, so it is also the only check that proves the
mod loads at all next to Space Age and the rest of the mod list.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent / "tests"
sys.path.insert(0, str(TESTS_DIR))

import context as ctx          # noqa: E402
import harness                 # noqa: E402


def run_dump(timeout=600):
    """Run the Factorio data stage and report whether it came back clean."""
    if not ctx.FACTORIO_EXE.exists():
        print("!! factorio.exe not found at %s" % ctx.FACTORIO_EXE)
        print("   set FACTORIO_DIR to override")
        return False

    print("-> %s --dump-data" % ctx.FACTORIO_EXE)
    started = time.time()
    try:
        completed = subprocess.run(
            [str(ctx.FACTORIO_EXE), "--dump-data"],
            capture_output=True, text=True, timeout=timeout,
            errors="replace")
    except subprocess.TimeoutExpired:
        print("!! timed out after %ds" % timeout)
        return False

    print("   exit %d in %.1fs" % (completed.returncode, time.time() - started))
    if completed.returncode != 0:
        tail = (completed.stdout or "") + (completed.stderr or "")
        print("\n".join(tail.strip().splitlines()[-40:]))
        return False

    # A clean exit code is necessary but not sufficient: a mod can log a
    # non-fatal complaint and still let the game start.
    log = ctx.USER_DIR / "factorio-current.log"
    if log.exists():
        suspicious = [
            line for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if ("rror" in line or "arning" in line)
            and "Error while" not in line
            and ctx.MOD_NAME in line
        ]
        if suspicious:
            print("!! the log mentions %s with an error/warning:" % ctx.MOD_NAME)
            for line in suspicious[:20]:
                print("   " + line)
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true",
                        help="regenerate data-raw-dump.json with factorio --dump-data")
    parser.add_argument("--dump-only", action="store_true",
                        help="run the data stage and stop")
    parser.add_argument("-k", dest="filter", default=None,
                        help="only run suites/tests whose name contains this")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print every passing assertion")
    args = parser.parse_args()

    print("mod:      %s" % ctx.MOD_DIR)
    print("factorio: %s" % ctx.FACTORIO_DIR)
    print("dump:     %s%s" % (ctx.DUMP_PATH,
                              "" if ctx.DUMP_PATH.exists() else "  (missing)"))

    if args.dump or args.dump_only:
        if not run_dump():
            print("\nRESULT: FAIL (data stage did not complete cleanly)")
            return 2
        print("   data stage OK")
        if args.dump_only:
            return 0

    # Imported for their @test side effects; order here is the report order.
    import test_manifest    # noqa: F401
    import test_graphics    # noqa: F401
    import test_data_stage  # noqa: F401
    import test_balance     # noqa: F401

    return harness.Report(verbose=args.verbose).run(only=args.filter).summary()


if __name__ == "__main__":
    sys.exit(main())
