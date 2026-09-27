# datasift-py — development justfile
# Run `just` or `just --list`.

python      := "python3"
pip         := python + " -m pip"
pytest      := python + " -m pytest"
ruff        := python + " -m ruff"
mypy        := python + " -m mypy"
mkdocs      := python + " -m mkdocs"
build       := python + " -m build"
twine       := python + " -m twine"

bench_dir   := env("BENCH_DIR", "/tmp/datasift-bench")
bench_rows  := env("BENCH_ROWS", "1000000")

src_dir     := "src/datasift"
test_dir    := "tests"

default:
    @just --list

install:
    {{pip}} install -e .

install-dev:
    {{pip}} install --upgrade pip
    {{pip}} install -e ".[dev]"

install-all:
    {{pip}} install --upgrade pip
    {{pip}} install -e ".[all]"

bootstrap: install-all
    @echo "✓ Environment ready."

test:
    {{pytest}}

test-fast:
    {{pytest}} -x

test-cov:
    {{pytest}} --cov=datasift --cov-report=term-missing --cov-report=html

lint:
    {{ruff}} check {{src_dir}} {{test_dir}} scripts benchmarks

format:
    {{ruff}} format {{src_dir}} {{test_dir}} scripts benchmarks

typecheck:
    {{mypy}} {{src_dir}}

check: lint typecheck test

bench-generate:
    {{python}} -m benchmarks.generate_data --rows {{bench_rows}} --out {{bench_dir}}

bench:
    {{python}} -m benchmarks.bench_data_vs_stream --data-dir {{bench_dir}} --rows {{bench_rows}}

docs:
    {{mkdocs}} serve

docs-build:
    {{mkdocs}} build --strict

build:
    {{build}}

build-check: build
    {{twine}} check dist/*

release-patch:
    {{python}} scripts/release.py patch

release-minor:
    {{python}} scripts/release.py minor

release-major:
    {{python}} scripts/release.py major

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf htmlcov/ .coverage coverage.xml build/ dist/ site/