#!/usr/bin/env python3
"""
Simple CLI around src.ipallocator functions.

Examples:
  python cli.py --overall 10.0.0.0/24 --existing 10.0.0.0/26 --existing 10.0.0.128/26 --prefix 26
"""
import argparse
import json
from src.ipallocator import find_available_subnets, can_allocate_prefix

def main():
    parser = argparse.ArgumentParser(description="Check if a subnet prefix can be allocated inside an overall CIDR without collisions.")
    parser.add_argument("--overall", "-o", required=True, help="Overall IPv4 CIDR (e.g. 10.0.0.0/24)")
    parser.add_argument("--existing", "-e", action="append", default=[], help="Existing subnet CIDR. Can be repeated.")
    parser.add_argument("--prefix", "-p", type=int, required=True, help="Requested prefix length (e.g. 26)")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    try:
        available = find_available_subnets(args.overall, args.existing, args.prefix)
        can_allocate = len(available) > 0
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    out = {
        "overall": args.overall,
        "existing": args.existing,
        "requested_prefix": args.prefix,
        "can_allocate": can_allocate,
        "available_count": len(available),
        "available_subnets": available,
    }

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Overall: {args.overall}")
        print(f"Existing: {', '.join(args.existing) if args.existing else '(none)'}")
        print(f"Requested prefix: /{args.prefix}")
        print(f"Can allocate: {'YES' if can_allocate else 'NO'}")
        print(f"Available subnets ({len(available)}):")
        for s in available:
            print(f"  {s}")

if __name__ == "__main__":
    main()
