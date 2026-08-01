# size — CLI Directory Size Analyzer

Analyze directory sizes with human-readable output and sorting. Recursively calculate directory sizes with depth control and file-type filtering. **Zero external dependencies** — pure Python stdlib.

```bash
curl -sS https://raw.githubusercontent.com/jrbobbyhansen-pixel/size/main/size.py -o /usr/local/bin/size
chmod +x /usr/local/bin/size
```

## Usage

```bash
# Current directory
size

# Specific path
size /var/log

# Top-level only
size --depth 1

# Only .log files
size --type .log

# Python files, 2 levels deep
size --type .py --depth 2 src

# Raw byte output
size --raw /tmp

# Skip sorting
size --no-sort

# Help
size --help

# Version
size --version
```

## Features

- **Recursive size calculation** — walks the full tree by default
- **Human-readable output** — auto-scales to KB/MB/GB/TB
- **Sort by size** — largest entries first (descending)
- **Configurable max depth** — `--depth N` limits recursion
- **File-type filter** — `--type .py` only counts matching extensions
- **Raw mode** — `--raw` outputs exact byte counts
- **Portable** — works on macOS, Linux, WSL

## Install via pip

```bash
pip install size
```

## Development

```bash
git clone https://github.com/jrbobbyhansen-pixel/size.git
cd size
python -m pytest -v
```

## Benchmarks

| Test | Files | manta-size | du (baseline) |
|------|-------|-----------|---------------|
| Small | 10 | 0.04s, 0.04MB | 0.004s, 0.07MB |
| Medium | 50 | 0.04s, 0.04MB | 0.004s, 0.06MB |
| Large | 100 | 0.04s, 0.04MB | 0.004s, 0.06MB |

Run your own: `python3 benchmark_size.py`

## License

MIT — see [LICENSE](LICENSE).
