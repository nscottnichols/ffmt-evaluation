"""Exercise relocated campaign tooling with the original unittest regressions."""
import importlib.util
from pathlib import Path
import unittest

DIRECTORY = Path(__file__).resolve().parents[1] / "tools/campaign_runner/test/conformance"
# These original files remain byte-preserved archival inputs. Their Make-level
# contracts are now tested by the library's test/test_infrastructure.py against
# its actual shared inventory, rather than an obsolete copy of portable-tests.mk.
RETIRED_BUILD_TESTS = {
    "test_build_registration.py",
    "test_cxx23_opt_in.py",
    "test_make_header_dependencies.py",
    "test_oracle_pin.py",
}


def load_tests(loader, tests, pattern):
    for source in sorted(DIRECTORY.glob("test_*.py")):
        if source.name in RETIRED_BUILD_TESTS:
            continue
        spec = importlib.util.spec_from_file_location("campaign_" + source.stem, source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests.addTests(loader.loadTestsFromModule(module))
    return tests
