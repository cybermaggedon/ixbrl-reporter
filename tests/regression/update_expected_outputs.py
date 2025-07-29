#!/usr/bin/env python3
"""
Helper script to update expected regression test outputs

This script runs the legacy test suite and helps review/update expected outputs
when intentional changes are made to report generation.
"""
import subprocess
import sys
import os
from pathlib import Path
import difflib
import argparse


def run_legacy_tests(project_root: Path) -> bool:
    """Run the legacy test suite
    
    Returns:
        True if tests passed, False otherwise
    """
    test_dir = project_root / "test"
    run_all_script = test_dir / "run_all"
    
    print("Running legacy regression tests...")
    result = subprocess.run(
        [str(run_all_script)],
        cwd=str(test_dir),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ All regression tests passed - no updates needed")
        return True
    else:
        print("✗ Regression tests failed - review needed")
        if result.stdout:
            print("\nOutput:")
            print(result.stdout)
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        return False


def show_differences(project_root: Path) -> dict:
    """Show differences between expected and actual outputs
    
    Returns:
        Dictionary mapping config names to their differences
    """
    output_dir = project_root / "output"
    log_dir = project_root / "log"
    
    differences = {}
    
    for kv_file in output_dir.glob("*.kv"):
        expected_file = log_dir / kv_file.name
        
        if expected_file.exists():
            expected_lines = expected_file.read_text().splitlines()
            actual_lines = kv_file.read_text().splitlines()
            
            if expected_lines != actual_lines:
                diff = list(difflib.unified_diff(
                    expected_lines,
                    actual_lines,
                    fromfile=f"expected ({kv_file.name})",
                    tofile=f"actual ({kv_file.name})",
                    lineterm=""
                ))
                differences[kv_file.stem] = diff
    
    return differences


def update_expected_outputs(project_root: Path, configs: list = None) -> None:
    """Update expected outputs with current results
    
    Args:
        project_root: Path to project root
        configs: List of config names to update (without .yaml), 
                or None to update all
    """
    output_dir = project_root / "output" 
    log_dir = project_root / "log"
    
    if configs:
        # Update only specified configs
        files_to_update = [f"{config}.kv" for config in configs]
    else:
        # Update all KV files
        files_to_update = [f.name for f in output_dir.glob("*.kv")]
    
    updated = []
    for filename in files_to_update:
        src = output_dir / filename
        dst = log_dir / filename
        
        if src.exists():
            print(f"Updating {filename}...")
            dst.write_text(src.read_text())
            updated.append(filename)
    
    print(f"\n✓ Updated {len(updated)} expected output files")


def main():
    parser = argparse.ArgumentParser(
        description="Update expected regression test outputs"
    )
    parser.add_argument(
        "--review", "-r",
        action="store_true",
        help="Review differences without updating"
    )
    parser.add_argument(
        "--update-all", "-a",
        action="store_true", 
        help="Update all expected outputs without review"
    )
    parser.add_argument(
        "--configs", "-c",
        nargs="+",
        help="Update specific configs only (e.g., -c unaud-micro aud-full)"
    )
    
    args = parser.parse_args()
    
    # Find project root
    project_root = Path(__file__).parent.parent.parent
    
    # First, run the legacy tests to generate new outputs
    passed = run_legacy_tests(project_root)
    
    if passed and not args.review:
        print("\nNo updates needed - all tests passing")
        return 0
    
    # Show differences
    differences = show_differences(project_root)
    
    if not differences:
        print("\nNo differences found")
        return 0
    
    print(f"\nFound differences in {len(differences)} files:")
    for config_name in sorted(differences.keys()):
        print(f"  - {config_name}")
    
    if args.review or (not args.update_all and not args.configs):
        # Show detailed differences
        print("\nDetailed differences:")
        for config_name, diff in sorted(differences.items()):
            print(f"\n{'='*60}")
            print(f"Config: {config_name}")
            print('='*60)
            print('\n'.join(diff[:50]))  # Show first 50 lines
            if len(diff) > 50:
                print(f"... and {len(diff) - 50} more lines")
    
    if args.review:
        return 0
    
    if args.update_all:
        print("\nUpdating all expected outputs...")
        update_expected_outputs(project_root)
    elif args.configs:
        print(f"\nUpdating specified configs: {', '.join(args.configs)}")
        update_expected_outputs(project_root, args.configs)
    else:
        # Interactive mode
        response = input("\nUpdate all expected outputs? [y/N]: ")
        if response.lower() == 'y':
            update_expected_outputs(project_root)
        else:
            print("Aborted - no files updated")
            return 1
    
    # Run pytest regression tests to confirm
    print("\nRunning pytest regression tests to confirm...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/regression/", "-v"],
        cwd=str(project_root)
    )
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())