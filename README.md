# IP Subnet Availability Checker

A small Python utility to determine whether a subnet with a given mask (prefix length) can be created inside a larger IPv4 CIDR without colliding with existing subnets.

Features:
- Check if any placement of the requested subnet size is available.
- List all available subnet placements.
- CLI and library usage.
- Unit tests using pytest.

Requirements
- Python 3.8+

Installation
1. Create a venv and install requirements:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

Usage (CLI)
- Check availability and list placements:
  python cli.py --overall 10.0.0.0/24 --existing 10.0.0.0/26 --existing 10.0.0.128/26 --prefix 26

- Short example:
  python cli.py -o 10.0.0.0/24 -e 10.0.0.0/26 -p 27

Library usage
```python
from src.ipallocator import find_available_subnets, can_allocate_prefix

overall = "10.0.0.0/24"
existing = ["10.0.0.0/26", "10.0.0.128/26"]
prefix = 27

available = find_available_subnets(overall, existing, prefix)
can_allocate = can_allocate_prefix(overall, existing, prefix)
```

Testing
- Run tests:
  pytest

Notes
- Works with