from unittest.mock import MagicMock, patch

import pytest

from cop_thief_mcp.services.reporting.gmail_client import build_gmail_service


def test_raises_clearly_when_client_secret_path_is_not_set(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET_PATH", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_CLIENT_SECRET_PATH"):
        build_gmail_service()


def test_uses_cached_valid_credentials_without_starting_a_new_oauth_flow(monkeypatch, tmp_path):
    client_secret = tmp_path / "client_google.json"
    client_secret.write_text("{}")
    (tmp_path / "token.json").write_text("{}")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_PATH", str(client_secret))

    cached_creds = MagicMock(valid=True)

    with (
        patch("cop_thief_mcp.services.reporting.gmail_client.Credentials.from_authorized_user_file",
              return_value=cached_creds),
        patch("cop_thief_mcp.services.reporting.gmail_client.InstalledAppFlow") as flow_cls,
        patch("cop_thief_mcp.services.reporting.gmail_client.build") as build_fn,
    ):
        build_gmail_service()

        flow_cls.from_client_secrets_file.assert_not_called()
        build_fn.assert_called_once_with("gmail", "v1", credentials=cached_creds)


def test_runs_a_new_oauth_flow_when_no_token_file_exists(monkeypatch, tmp_path):
    client_secret = tmp_path / "client_google.json"
    client_secret.write_text("{}")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET_PATH", str(client_secret))

    new_creds = MagicMock(valid=True)
    new_creds.to_json.return_value = "{}"

    with (
        patch("cop_thief_mcp.services.reporting.gmail_client.InstalledAppFlow") as flow_cls,
        patch("cop_thief_mcp.services.reporting.gmail_client.build") as build_fn,
    ):
        flow_cls.from_client_secrets_file.return_value.run_local_server.return_value = new_creds

        build_gmail_service()

        flow_cls.from_client_secrets_file.assert_called_once_with(str(client_secret), ["https://www.googleapis.com/auth/gmail.compose"])
        build_fn.assert_called_once_with("gmail", "v1", credentials=new_creds)
    assert (tmp_path / "token.json").exists()
