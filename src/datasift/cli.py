"""Command-line interface for datasift."""

import argparse
import sys
from typing import List, Optional

from .core import convert, dump, query_file, supported_formats
from .exceptions import DataSiftError


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="datasift",
        description="Convert and query JSON, YAML, TOML, CSV, XML, and JSONL files.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="Convert between formats.")
    c.add_argument("input", help="Input file path.")
    c.add_argument("output", help="Output file path.")
    c.add_argument("-if", "--input-format", default=None)
    c.add_argument("-of", "--output-format", default=None)
    c.add_argument("-q", "--query", default=None)

    q = sub.add_parser("query", help="Run a query and print the result.")
    q.add_argument("input", help="Input file path.")
    q.add_argument("expression", help="Query expression.")
    q.add_argument("-if", "--input-format", default=None)
    q.add_argument("-of", "--output-format", default="json")

    sub.add_parser("formats", help="List supported formats.")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "convert":
            convert(
                args.input,
                args.output,
                input_fmt=args.input_format,
                output_fmt=args.output_format,
                query_expr=args.query,
            )
            return 0

        if args.command == "query":
            result = query_file(args.input, args.expression, fmt=args.input_format)
            text = dump(result, fmt=args.output_format)
            sys.stdout.write(text)
            return 0

        if args.command == "formats":
            for name in supported_formats():
                print(name)
            return 0

    except DataSiftError as exc:
        print(f"datasift: error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"datasift: unexpected error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
