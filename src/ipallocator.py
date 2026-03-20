"""
IP subnet allocation helpers.

Functions:
- candidates_with_collisions(overall_cidr: str, existing_cidrs: list[str] | str, target_prefix: int) -> list[dict]
- generate_available_candidates(overall_cidr: str, existing_cidrs: list[str] | str, target_prefix: int) -> list[dict]
- find_available_subnets(overall_cidr: str, existing_cidrs: list[str] | str, target_prefix: int) -> list[str]
- can_allocate_prefix(overall_cidr: str, existing_cidrs: list[str] | str, target_prefix: int) -> bool
"""
from ipaddress import IPv4Network
from typing import List, Dict, Iterable, Union


def _normalize_existing(existing_cidrs: Union[Iterable[str], str]) -> List[str]:
    """
    Accept either an iterable of CIDR strings or a single multi-line string.
    Return a flattened list of stripped non-empty CIDR strings. If any element itself
    contains newlines, split it into separate entries.
    """
    if existing_cidrs is None:
        return []

    lines: List[str] = []

    # If top-level is a string, split it into lines
    if isinstance(existing_cidrs, str):
        raw_items = existing_cidrs.splitlines()
    else:
        # Try to iterate; each item may itself be a multi-line string, so split each one
        try:
            raw_items = list(existing_cidrs)
        except TypeError:
            raw_items = [str(existing_cidrs)]

    for item in raw_items:
        if item is None:
            continue
        # Convert non-strings to string, then split on newlines and extend
        if not isinstance(item, str):
            item = str(item)
        for sub in item.splitlines():
            sub = sub.strip()
            if sub:
                lines.append(sub)

    return lines


def _parse_networks(overall_cidr: str, existing_cidrs: Union[Iterable[str], str]):
    if not overall_cidr:
        raise ValueError("overall_cidr is required")

    overall = None
    try:
        overall = IPv4Network(overall_cidr, strict=False)
    except Exception as exc:
        raise ValueError(f"invalid overall CIDR '{overall_cidr}': {exc}")

    existing_list = _normalize_existing(existing_cidrs)
    existing_networks = []
    for cidr in existing_list:
        try:
            existing_networks.append(IPv4Network(cidr, strict=False))
        except Exception as exc:
            raise ValueError(f"invalid existing CIDR '{cidr}': {exc}")

    return overall, existing_networks


def candidates_with_collisions(overall_cidr: str, existing_cidrs: Union[Iterable[str], str], target_prefix: int) -> List[Dict]:
    """
    Enumerate candidate subnets of size target_prefix inside overall_cidr and, for each candidate,
    return a dict with:
      - 'subnet': string representation of the candidate subnet
      - 'overlaps': list of existing subnet strings that overlap this candidate (may be empty)
    """
    overall, existing = _parse_networks(overall_cidr, existing_cidrs)

    if target_prefix < overall.prefixlen:
        raise ValueError(f"target prefix {target_prefix} is larger network than overall {overall.prefixlen} (must be >= {overall.prefixlen})")

    if target_prefix > 32 or target_prefix < 0:
        raise ValueError("prefix length must be between 0 and 32")

    candidates = list(overall.subnets(new_prefix=target_prefix))

    result = []
    for cand in candidates:
        overlaps = []
        for ex in existing:
            if cand.overlaps(ex):
                overlaps.append(str(ex))
        result.append({"subnet": str(cand), "overlaps": overlaps})
    return result


def generate_available_candidates(overall_cidr: str, existing_cidrs: Union[Iterable[str], str], target_prefix: int) -> List[Dict]:
    """
    Return only non-conflicting candidate subnets (i.e., those that do not overlap any existing subnets).
    Each returned dict has the same shape as candidates_with_collisions but 'overlaps' will be an empty list.
    """
    candidates = candidates_with_collisions(overall_cidr, existing_cidrs, target_prefix)
    available = [ {"subnet": c["subnet"], "overlaps": []} for c in candidates if not c["overlaps"] ]
    return available


def find_available_subnets(overall_cidr: str, existing_cidrs: Union[Iterable[str], str], target_prefix: int) -> List[str]:
    """
    Return a list of available subnets (as strings) of size target_prefix that fit inside overall_cidr
    and do not overlap any of the existing_cidrs.
    """
    candidates = generate_available_candidates(overall_cidr, existing_cidrs, target_prefix)
    available = [c["subnet"] for c in candidates]
    return available


def can_allocate_prefix(overall_cidr: str, existing_cidrs: Union[Iterable[str], str], target_prefix: int) -> bool:
    """
    Returns True if at least one placement exists for a subnet with target_prefix inside overall_cidr
    without colliding with any existing_cidrs.
    """
    available = find_available_subnets(overall_cidr, existing_cidrs, target_prefix)
    return len(available) > 0