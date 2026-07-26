"""Offline tests for the Places integration: payload parsing and the TTL cache.

Nothing here touches the network -- ``fetch_place`` is the only function that
does, and it is monkeypatched out.
"""

from __future__ import annotations

import httpx

from pitch_doctor.integrations import places

_RICH_PAYLOAD = {
    "places": [
        {
            "id": "ChIJabc123",
            "displayName": {"text": "Joe's Plumbing", "languageCode": "en"},
            "formattedAddress": "100 Main St, Houston, TX 77002",
            "primaryType": "plumber",
            "primaryTypeDisplayName": {"text": "Plumber"},
            "businessStatus": "OPERATIONAL",
            "regularOpeningHours": {"weekdayDescriptions": ["Monday: 8-5"]},
            "photos": [{"name": "p1"}, {"name": "p2"}],
            "rating": 4.6,
            "userRatingCount": 88,
            "websiteUri": "https://joesplumbing.test",
            "nationalPhoneNumber": "(713) 555-0100",
        }
    ]
}

_THIN_PAYLOAD = {
    "places": [
        {
            "id": "ChIJthin",
            "displayName": {"text": "Corner Barber"},
            "businessStatus": "OPERATIONAL",
        }
    ]
}


def test_field_mask_asks_only_for_fields_the_check_reads():
    # Every field here is billed on every uncached lookup, so an accidental
    # addition is a cost regression.
    assert places.FIELD_MASK.split(",") == [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.primaryType",
        "places.primaryTypeDisplayName",
        "places.businessStatus",
        "places.photos",
        "places.regularOpeningHours",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
    ]
    # Reviews are the most expensive tier and still hide owner replies.
    assert "places.reviews" not in places.FIELD_MASK


def test_parse_rich_payload():
    profile = places.parse_place(_RICH_PAYLOAD)
    assert profile.found
    assert profile.name == "Joe's Plumbing"
    assert profile.primary_type == "Plumber"
    assert profile.has_hours
    assert profile.photo_count == 2
    assert profile.rating == 4.6
    assert profile.review_count == 88
    assert profile.website_uri == "https://joesplumbing.test"
    # Owner replies are unknowable through this API, never zero.
    assert profile.reviews_without_reply is None


def test_parse_thin_payload_defaults_to_empty_not_missing():
    profile = places.parse_place(_THIN_PAYLOAD)
    assert profile.found
    assert profile.has_hours is False
    assert profile.photo_count == 0
    assert profile.review_count == 0
    assert profile.rating is None


def test_parse_empty_payload_is_not_found():
    assert places.parse_place({"places": []}).found is False
    assert places.parse_place({}).found is False


def test_build_query_drops_a_missing_city():
    assert places.build_query("Joe's Plumbing", "Houston") == "Joe's Plumbing, Houston"
    assert places.build_query("Joe's Plumbing", None) == "Joe's Plumbing"
    assert places.build_query("Joe's Plumbing", "  ") == "Joe's Plumbing"


def test_cache_round_trip(tmp_path):
    cache = tmp_path / "places.db"
    assert places.read_cache("joe, houston", cache) is None
    places.write_cache("joe, houston", _RICH_PAYLOAD, cache)
    assert places.read_cache("joe, houston", cache) == _RICH_PAYLOAD


def test_cache_entry_past_its_ttl_is_ignored(tmp_path):
    cache = tmp_path / "places.db"
    places.write_cache("joe, houston", _RICH_PAYLOAD, cache)
    assert places.read_cache("joe, houston", cache, ttl=-1) is None


def test_cache_survives_an_unwritable_path(tmp_path):
    # A broken cache must degrade to "no cache", never take down a scan.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    doomed = blocker / "nested" / "places.db"
    assert places.read_cache("joe", doomed) is None
    places.write_cache("joe", _RICH_PAYLOAD, doomed)  # must not raise


async def test_lookup_without_a_business_name_is_degraded_not_a_miss(tmp_path):
    profile = await places.lookup_business(None, "Houston", cache_path=tmp_path / "c.db")
    assert profile.found is False
    assert profile.error == "no business name to search for"


async def test_lookup_without_an_api_key_is_degraded(monkeypatch, tmp_path):
    monkeypatch.delenv(places.API_KEY_ENV_VAR, raising=False)
    profile = await places.lookup_business("Joe's Plumbing", "Houston", cache_path=tmp_path / "c.db")
    assert profile.found is False
    assert places.API_KEY_ENV_VAR in profile.error


async def test_lookup_hits_the_api_once_then_serves_from_cache(monkeypatch, tmp_path):
    monkeypatch.setenv(places.API_KEY_ENV_VAR, "test-key")
    cache = tmp_path / "places.db"
    calls = []

    async def fake_fetch(query, timeout, key):
        calls.append(query)
        return _RICH_PAYLOAD

    monkeypatch.setattr(places, "fetch_place", fake_fetch)

    first = await places.lookup_business("Joe's Plumbing", "Houston", cache_path=cache)
    second = await places.lookup_business("Joe's Plumbing", "Houston", cache_path=cache)

    assert calls == ["Joe's Plumbing, Houston"]
    assert first.found and second.found
    assert first.from_cache is False
    assert second.from_cache is True


async def test_lookup_turns_an_api_error_into_a_degraded_profile(monkeypatch, tmp_path):
    monkeypatch.setenv(places.API_KEY_ENV_VAR, "test-key")

    async def failing_fetch(query, timeout, key):
        raise httpx.ConnectError("network unreachable")

    monkeypatch.setattr(places, "fetch_place", failing_fetch)

    profile = await places.lookup_business(
        "Joe's Plumbing", "Houston", cache_path=tmp_path / "places.db"
    )
    assert profile.found is False
    assert "network unreachable" in profile.error


async def test_a_failed_lookup_is_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv(places.API_KEY_ENV_VAR, "test-key")
    cache = tmp_path / "places.db"

    async def failing_fetch(query, timeout, key):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(places, "fetch_place", failing_fetch)
    await places.lookup_business("Joe's Plumbing", "Houston", cache_path=cache)
    assert places.read_cache("Joe's Plumbing, Houston", cache) is None


def test_default_cache_path_honours_the_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv(places.CACHE_DIR_ENV_VAR, str(tmp_path))
    assert places.default_cache_path() == tmp_path / places.CACHE_FILENAME


async def test_a_stale_cache_entry_is_refetched(monkeypatch, tmp_path):
    monkeypatch.setenv(places.API_KEY_ENV_VAR, "test-key")
    cache = tmp_path / "places.db"
    places.write_cache("Joe's Plumbing, Houston", _THIN_PAYLOAD, cache)
    calls = []

    async def fake_fetch(query, timeout, key):
        calls.append(query)
        return _RICH_PAYLOAD

    monkeypatch.setattr(places, "fetch_place", fake_fetch)
    profile = await places.lookup_business(
        "Joe's Plumbing", "Houston", cache_path=cache, ttl=-1
    )
    assert calls == ["Joe's Plumbing, Houston"]
    assert profile.name == "Joe's Plumbing"
