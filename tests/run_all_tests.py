"""
EnterpriseAIMailOPs_MIPRO Test Suite Runner
Executes multi-tier test suites (Tiers 1-5) and generates a structured summary report.

Usage:
    python tests/run_all_tests.py [--tier 1|2|3|4|5|all] [--verbose]
"""

import argparse
import os
import subprocess
import sys
import time


TIER_PATHS = {
    "tier1": "tests/tier1_features",
    "tier2": "tests/tier2_boundaries",
    "tier3": "tests/tier3_pairwise",
    "tier4": "tests/tier4_scenarios",
    "tier5": "tests/tier5_adversarial",
}


def run_pytest(target_path: str, verbose: bool = False) -> tuple[int, str]:
    """Execute pytest against the specified path and return (exit_code, output)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        target_path,
        "-v" if verbose else "-q",
        "--tb=short",
    ]
    start = time.time()
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    duration = time.time() - start
    return proc.returncode, proc.stdout + proc.stderr, duration


def main():
    parser = argparse.ArgumentParser(description="EnterpriseAIMailOPs_MIPRO Test Runner")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "5", "all"], default="all")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print(" EnterpriseAIMailOPs_MIPRO — Automated Multi-Tier Test Suite")
    print("=" * 70)

    selected_tiers = (
        TIER_PATHS.items()
        if args.tier == "all"
        else [(f"tier{args.tier}", TIER_PATHS[f"tier{args.tier}"])]
    )

    results = {}
    total_passed = 0
    total_failed = 0

    for tier_name, tier_path in selected_tiers:
        print(f"\n[Running] {tier_name.upper()} ({tier_path})...")
        code, output, duration = run_pytest(tier_path, args.verbose)
        results[tier_name] = {
            "code": code,
            "output": output,
            "duration": duration,
        }

        # Parse passed/failed from pytest output
        for line in output.splitlines():
            if "passed" in line or "failed" in line:
                print(f"  -> {line.strip()} ({duration:.2f}s)")
                break

    print("\n" + "=" * 70)
    print(" Execution Summary")
    print("=" * 70)
    any_failed = False
    for tier_name, res in results.items():
        status_str = "PASS" if res["code"] == 0 else f"FAIL (exit {res['code']})"
        if res["code"] != 0:
            any_failed = True
        print(f"  {tier_name.upper():<10} : {status_str} in {res['duration']:.2f}s")

    print("=" * 70)
    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
