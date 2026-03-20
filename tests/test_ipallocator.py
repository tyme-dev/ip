import pytest
from src.ipallocator import find_available_subnets, can_allocate_prefix

def test_basic_allocation_available():
    overall = "10.0.0.0/24"
    existing = ["10.0.0.0/26", "10.0.0.128/26"]
    # /27 subnets should be available (each /26 equals two /27s, but only two /26 are taken; there are 8 /27s total)
    assert can_allocate_prefix(overall, existing, 27) is True
    avail = find_available_subnets(overall, existing, 27)
    assert len(avail) > 0
    # ensure none of the available overlap existing
    for a in avail:
        for ex in existing:
            assert not (__import__("ipaddress").ip_network(a).overlaps(__import__("ipaddress").ip_network(ex))


def test_full_collision_no_space():
    overall = "10.0.0.0/24"
    # fill /26s to cover entire /24
    existing = [
        "10.0.0.0/26",
        "10.0.0.64/26",
        "10.0.0.128/26",
        "10.0.0.192/26",
    ]
    # requesting /26 should be impossible
    assert can_allocate_prefix(overall, existing, 26) is False
    assert find_available_subnets(overall, existing, 26) == []


def test_invalid_prefix_too_small():
    overall = "10.0.0.0/24"
    existing = []
    with pytest.raises(ValueError):
        # prefix smaller (less specific) than overall is invalid, e.g., request /16 inside /24
        find_available_subnets(overall, existing, 16)
