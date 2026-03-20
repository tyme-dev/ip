"""
IP subnet allocation helpers.

Functions:
- find_available_subnets(overall_cidr: str, existing_cidrs: list[str], target_prefix: int) -> list[str]
- can_allocate_prefix(overall_cidr: str, existing_cidrs: list[str], target_prefix: int) -> bool
"""

from ipaddress import IPv4Network, IPv4Address
from typing import List


def _parse_networks(overall_cidr: str, existing_cidrs: List[str]):
    overall = IPv4Network(overall_cidr, strict=False)
    existing = [IPv4Network(cidr, strict=False) for cidr in existing_cidrs]
    return overall, existing


def find_available_subnets(overall_cidr: str, existing_cidrs: List[str], target_prefix: int) -> List[str]:
    """
    Return a list of available subnets (as strings) of size target_prefix that fit inside overall_cidr
    and do not overlap any of the existing_cidrs.

    Params:
    - overall_cidr: e.g., "10.0.0.0/24"
    - existing_cidrs: list of strings e.g., ["10.0.0.0/26", "10.0.0.128/26"]
    - target_prefix: integer e.g., 26

    Returns:
    - list of subnet strings like "10.0.0.0/26"
    """
    overall, existing = _parse_networks(overall_cidr, existing_cidrs)

    if target_prefix < overall.prefixlen:
        raise ValueError(f"target prefix {target_prefix} is larger network than overall {overall.prefixlen} (must be >= {overall.prefixlen})")

    if target_prefix > 32 or target_prefix < 0:
        raise ValueError("prefix length must be between 0 and 32")

    # Enumerate candidate subnets
    candidates = list(overall.subnets(new_prefix=target_prefix))

    available = []
    for cand in candidates:
        collision = False
        for ex in existing:
            # If candidate overlaps existing, we can't use it
            if cand.overlaps(ex):
                collision = True
                break
        if not collision:
            available.append(str(cand))

    return available


def can_allocate_prefix(overall_cidr: str, existing_cidrs: List[str], target_prefix: int) -> bool:
    """
    Returns True if at least one placement exists for a subnet with target_prefix inside overall_cidr
    without colliding with any existing_cidrs.
    """
    available = find_available_subnets(overall_cidr, existing_cidrs, target_prefix)
    return len(available) > 0
