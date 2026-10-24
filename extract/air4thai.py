"""Extract the latest hourly readings for every Air4Thai monitoring station."""

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

AIR4THAI_URL = os.getenv(
    "AIR4THAI_URL", "https://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
)
RAW_DIR = Path(os.getenv("DATA_DIR", "data")) / "raw" / "air4thai"
TIMEOUT_SECONDS = 30
INTERMEDIATES = Path(__file__).parent / "certs" / "air4thai_intermediates.pem"


class Air4ThaiError(RuntimeError):
    """The API answered, but not with the payload we expect."""


@cache
def ca_bundle() -> str:
    """certifi's CA bundle plus the intermediates the Air4Thai server fails to send.

    The server serves a Let's Encrypt leaf with Sectigo intermediates, so
    verification fails on any client that does not fetch missing issuers itself.
    """
    bundle = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
    with bundle:
        bundle.write(Path(certifi.where()).read_text())
        bundle.write(INTERMEDIATES.read_text())
    return bundle.name


def build_session(retries: int = 3) -> requests.Session:
    """Session that retries transient failures with exponential backoff."""
    retry = Retry(
        total=retries,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.verify = ca_bundle()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def fetch_latest(session: requests.Session | None = None) -> dict:
    """Return the raw API payload: {"stations": [...]}."""
    session = session or build_session()
    response = session.get(AIR4THAI_URL, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise Air4ThaiError("Response is not valid JSON") from exc

    stations = payload.get("stations") if isinstance(payload, dict) else None
    if not isinstance(stations, list) or not stations:
        raise Air4ThaiError("Response has no 'stations' list")

    logger.info("Fetched %d stations from Air4Thai", len(stations))
    return payload


def save_raw(payload: dict, fetched_at: datetime, raw_dir: Path = RAW_DIR) -> Path:
    """Write the payload untouched, partitioned by fetch date (UTC)."""
    out_dir = raw_dir / f"dt={fetched_at:%Y-%m-%d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{fetched_at:%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved raw payload to %s", path)
    return path


def run(raw_dir: Path = RAW_DIR) -> Path:
    fetched_at = datetime.now(timezone.utc)
    return save_raw(fetch_latest(), fetched_at, raw_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(run(args.raw_dir))


if __name__ == "__main__":
    main()
