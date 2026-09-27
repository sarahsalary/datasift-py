# GitHub Actions scripts

Helper scripts used by `.github/workflows/benchmark.yml`.

## `format_benchmark_comment.py`

Reads two benchmark JSON files (PR branch and base branch), compares
them, and writes a Markdown PR comment.

The comment starts with a hidden marker `<!-- datasift-benchmark -->`
so the workflow can find and update the same comment on subsequent
pushes instead of creating a new one every time.

## `check_regression.py`

Reads the same JSON files and exits with code 1 if any scenario is
more than `--threshold` percent slower than the base branch.