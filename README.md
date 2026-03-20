# IP Subnet Availability Checker

A small Python utility to determine whether a subnet with a given mask (prefix length) can be created inside a larger IPv4 CIDR without colliding with existing subnets. This project includes:

- a library (src/ipallocator.py) with allocation logic,
- a CLI (cli.py),
- unit tests (pytest),
- a simple Web UI (Flask) for interactive checks.

Features
- Check if any placement of the requested subnet size is available.
- List all available subnet placements.
- CLI, library, and Web UI usage.
- Unit tests using pytest.

Requirements
- Python 3.8+
- The requirements.txt in this repo includes the needed packages.

Quick installation (local/dev)
1. Clone and enter the repo:
   git clone https://github.com/tyme-dev/ip.git
   cd ip

2. Create and activate a virtualenv:
   python -m venv .venv
   source .venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

Library usage
```python
from src.ipallocator import find_available_subnets, can_allocate_prefix

overall = "10.0.0.0/24"
existing = ["10.0.0.0/26", "10.0.0.128/26"]
prefix = 27

available = find_available_subnets(overall, existing, prefix)
can_allocate = can_allocate_prefix(overall, existing, prefix)
```

CLI usage
- Check availability and list placements:
  python cli.py --overall 10.0.0.0/24 --existing 10.0.0.0/26 --existing 10.0.0.128/26 --prefix 26

- Short example:
  python cli.py -o 10.0.0.0/24 -e 10.0.0.0/26 -p 27

Run tests
- Run unit tests:
  pytest

Web UI (development)
- The web UI is a minimal development UI built with Flask. It provides an interactive form and a JSON API endpoint.

Run the web UI (development):
1. Activate your venv (see above).
2. Start the web app:
   python -m webapp.app
3. Open: http://127.0.0.1:8000

Or with flask CLI:
   export FLASK_APP=webapp.app:create_app
   flask run --host=0.0.0.0 --port=8000

Web UI usage
- Enter an overall IPv4 CIDR (e.g. `10.0.0.0/24`).
- Enter existing subnets separated by newlines (each a CIDR).
- Enter the requested prefix length (e.g. `26`).
- Submit to see available placements and a JSON view.

API
- POST /api/check
  - Request JSON:
    {
      "overall": "10.0.0.0/24",
      "existing": ["10.0.0.0/26", "10.0.0.128/26"],
      "prefix": 27
    }
  - Response JSON:
    {
      "can_allocate": true,
      "available_subnets": ["10.0.0.0/27", ...]
    }

Notes and next steps
- Works with IPv4 only (can be extended to IPv6).
- The web UI is a small local development interface. For production: run behind a WSGI server, add input validation, rate limiting, logging, and CSRF protection.
- I can:
  - add a license,
  - add a .gitignore,
  - add GitHub Actions to run pytest on push,
  - implement IPv6 support or different allocation strategies (first-fit, best-fit, allocate N contiguous blocks),
  - containerize the app with Docker.