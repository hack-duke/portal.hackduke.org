from types import SimpleNamespace
from resend_reported_duquantum_invitations import choose_registration, roster_repair


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


def test_repair_requires_unique_final_team_and_preserves_declined_consents():
    registered = row("a@example.org", id="registration", source="google_forms_csv", admission_status="revoked", rsvp_status="declined", attendance_commitment=True, photo_release_consent=True, mlh_code_of_conduct_consent=True, data_sharing_consent=True, team_membership=None)
    member = SimpleNamespace(id="member", registration_id=None, match_status="unmatched")
    repair = roster_repair([registered.normalized_email], [registered], [member], [registered])
    assert repair["action"] == "restore"
    registered.photo_release_consent = False
    assert roster_repair([registered.normalized_email], [registered], [member], [registered]) is None
    registered.photo_release_consent = True
    assert roster_repair([registered.normalized_email], [registered], [member, member], [registered]) is None


def test_new_registration_is_blocked_if_same_name_already_registered_elsewhere():
    member = SimpleNamespace(id="member", registration_id=None, match_status="unmatched", display_name="Test Person", first_name="Test", last_name="Person")
    assert roster_repair(["a@example.org"], [], [member], [SimpleNamespace(first_name="Test", last_name="Person")]) is None
    repair = roster_repair(["a@example.org"], [], [member], [])
    assert repair["action"] == "create"
    assert repair["email"] == "a@example.org"
