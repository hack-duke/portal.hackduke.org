from types import SimpleNamespace
from resend_reported_duquantum_invitations import choose_registration


def row(email, **overrides):
    values = dict(normalized_email=email, admission_status="accepted", rsvp_status="confirmed")
    values.update(overrides)
    return SimpleNamespace(**values)


def test_alternate_addresses_resolve_to_the_one_registered_identity():
    registered = row("primary@example.org")
    assert choose_registration(["alternate@example.org", "primary@example.org"], [registered]) == (registered, None)


def test_multiple_accounts_and_unregistered_people_are_not_silently_selected():
    assert choose_registration(["a@example.org", "b@example.org"], [row("a@example.org"), row("b@example.org")]) == (None, "ambiguous_registration")
    assert choose_registration(["a@example.org"], []) == (None, "missing_registration")


def test_resend_cannot_turn_an_ineligible_registration_into_an_invitation():
    for override in ({"admission_status": "rejected"}, {"rsvp_status": "pending"}):
        assert choose_registration(["a@example.org"], [row("a@example.org", **override)]) == (None, "ineligible_registration")
