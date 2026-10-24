import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from extract import air4thai

FIXTURE = Path(__file__).parent / "fixtures" / "air4thai_sample.json"


class FakeResponse:
    def __init__(self, body: str, status: int = 200):
        self.text = body
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise air4thai.requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response

    def get(self, url, timeout):
        return self.response


def test_fetch_latest_returns_stations():
    body = FIXTURE.read_text(encoding="utf-8")
    payload = air4thai.fetch_latest(FakeSession(FakeResponse(body)))
    assert len(payload["stations"]) == 4
    assert payload["stations"][0]["stationID"] == "119t"


@pytest.mark.parametrize("body", ["<html>maintenance</html>", "{}", '{"stations": []}', "[]"])
def test_fetch_latest_rejects_bad_payload(body):
    with pytest.raises(air4thai.Air4ThaiError):
        air4thai.fetch_latest(FakeSession(FakeResponse(body)))


def test_fetch_latest_raises_on_http_error():
    with pytest.raises(air4thai.requests.HTTPError):
        air4thai.fetch_latest(FakeSession(FakeResponse("", status=503)))


def test_save_raw_partitions_by_date(tmp_path):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fetched_at = datetime(2026, 10, 24, 3, 15, 0, tzinfo=timezone.utc)

    path = air4thai.save_raw(payload, fetched_at, tmp_path)

    assert path == tmp_path / "dt=2026-10-24" / "20261024T031500Z.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == payload
    assert "สวนสาธารณะธารา" in path.read_text(encoding="utf-8")


def test_session_trusts_air4thai_intermediates():
    session = air4thai.build_session()
    bundle = Path(session.verify).read_text()
    assert air4thai.INTERMEDIATES.read_text() in bundle
    assert bundle.count("BEGIN CERTIFICATE") > 100
