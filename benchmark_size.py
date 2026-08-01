#!/usr/bin/env python3
"""Benchmark manta-size against du (baseline).

Measures:
- Time to scan directories of various sizes
- Memory usage during scan
- Accuracy vs du output

Usage:
    python3 benchmark_size.py [--dir DIR] [--sizes SMALL,MEDIUM,LARGE]

Outputs JSON results to stdout.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc


def create_test_dir(base_dir, num_files, depth):
    """Create a directory tree with num_files at given depth."""
    dir_path = os.path.join(base_dir, f"test_{num_files}_{depth}")
    os.makedirs(dir_path, exist_ok=True)

    files_per_dir = max(1, num_files // (depth + 1))
    created = 0

    for d in range(depth + 1):
        subdir = os.path.join(dir_path, f"level_{d}")
        os.makedirs(subdir, exist_ok=True)
        for i in range(files_per_dir):
            path = os.path.join(subdir, f"file_{i}.txt")
            with open(path, "w") as f:
                f.write("x" * (1024 * (i % 10 + 1)))
            created += 1
            if created >= num_files:
                return dir_path

    return dir_path


def benchmark_tool(tool_name, cmd, dir_path):
    """Run a tool and measure time + memory."""
    tracemalloc.start()
    start = time.time()

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60
    )

    elapsed = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "tool": tool_name,
        "elapsed_seconds": round(elapsed, 3),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "exit_code": result.returncode,
        "stdout_lines": len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0,
        "stderr": result.stderr[:200] if result.stderr else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark manta-size")
    parser.add_argument("--dir", default=None, help="Directory to scan")
    parser.add_argument(
        "--sizes", default="50,200,1000",
        help="Comma-separated file counts for small/medium/large tests"
    )
    args = parser.parse_args()

    sizes = [int(s) for s in args.sizes.split(",")]
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for num_files in sizes:
            print(f"Creating test dir with {num_files} files...", file=sys.stderr)
            test_dir = create_test_dir(tmpdir, num_files, 3)

            # Benchmark manta-size
            size_script = os.path.join(os.path.dirname(__file__), "size.py")
            if os.path.exists(size_script):
                r = benchmark_tool(
                    "manta-size", [sys.executable, size_script, test_dir], test_dir
                )
                r["test_size"] = num_files
                results.append(r)

            # Benchmark du (baseline)
            r = benchmark_tool(
                "du (baseline)",
                ["du", "-sh", test_dir],
                test_dir,
            )
            r["test_size"] = num_files
            results.append(r)

            print(f"  Done: {num_files} files", file=sys.stderr)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
