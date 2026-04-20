from mailer.tokens import make_unsubscribe_token, parse_unsubscribe_token


def test_roundtrip():
    t = make_unsubscribe_token("secret", email="foo@bar.ch", campaign_id=7)
    parsed = parse_unsubscribe_token("secret", t)
    assert parsed == ("foo@bar.ch", 7)


def test_email_lowercased_on_sign():
    t = make_unsubscribe_token("secret", email="FOO@BAR.CH", campaign_id=7)
    email, _ = parse_unsubscribe_token("secret", t)
    assert email == "foo@bar.ch"


def test_bad_secret_rejected():
    t = make_unsubscribe_token("secret", email="foo@bar.ch", campaign_id=7)
    assert parse_unsubscribe_token("other-secret", t) is None


def test_garbage_rejected():
    assert parse_unsubscribe_token("secret", "not-a-token") is None
    assert parse_unsubscribe_token("secret", "") is None
