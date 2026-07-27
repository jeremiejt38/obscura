import json

from obscura import updater


def test_uses_recent_cached_update(monkeypatch, tmp_path):
    state = tmp_path / "update-check.json"
    state.write_text(
        json.dumps(
            {
                "checked_at": updater.time.time(),
                "update": {
                    "version": "v0.1.1",
                    "asset_url": "https://example.test/obscura-linux",
                    "checksum_url": "https://example.test/obscura-linux.sha256",
                    "critical": False,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(updater, "_check_state_path", lambda: state)

    update = updater.check_for_update(interval_hours=24)

    assert update is not None
    assert update.version == "v0.1.1"


def test_forced_check_requests_release(monkeypatch, tmp_path):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(updater, "_check_state_path", lambda: tmp_path / "update-check.json")
    monkeypatch.setattr(updater.platform, "system", lambda: "Linux")
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())
    monkeypatch.setattr(
        updater.json,
        "load",
        lambda _response: {
            "tag_name": "v0.1.1",
            "body": "[critical]",
            "assets": [
                {"name": "obscura-linux", "browser_download_url": "https://example.test/app"},
                {"name": "obscura-linux.sha256", "browser_download_url": "https://example.test/app.sha256"},
            ],
        },
    )

    update = updater.check_for_update(force=True)

    assert update is not None
    assert update.critical
