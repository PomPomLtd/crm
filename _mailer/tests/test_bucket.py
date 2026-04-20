from collections import Counter

from mailer.bucket import VARIANTS, assign_variant


def test_assignment_is_deterministic():
    assert assign_variant("foo@bar.ch") == assign_variant("foo@bar.ch")


def test_assignment_is_case_insensitive():
    assert assign_variant("FOO@BAR.CH") == assign_variant("foo@bar.ch")
    assert assign_variant("  Foo@Bar.CH  ") == assign_variant("foo@bar.ch")


def test_assignment_uses_all_variants():
    seen = {assign_variant(f"u{i}@x.ch") for i in range(300)}
    assert seen == set(VARIANTS)


def test_assignment_is_roughly_uniform():
    counts = Counter(assign_variant(f"u{i}@x.ch") for i in range(3000))
    for v in VARIANTS:
        assert 900 <= counts[v] <= 1100, (v, counts[v])


def test_salt_changes_assignment_distribution():
    # Different salts should produce different individual assignments for
    # at least some recipients (not bitwise identical distributions).
    addrs = [f"u{i}@x.ch" for i in range(200)]
    a = [assign_variant(e, salt="c1") for e in addrs]
    b = [assign_variant(e, salt="c2") for e in addrs]
    assert a != b
