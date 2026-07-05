"""Builds the shared Gmail API service, reusing the OAuth client/token already
set up for this Google account (see GOOGLE_CLIENT_SECRET_PATH). The token is
cached alongside the client secret file, exactly like the pattern already
validated in this environment's calendar/draft test program.

`gmail.compose` is used rather than `gmail.send`: per Google's own scope
documentation it covers both draft management and actually sending messages,
so the already-granted token needs no new consent.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def _token_path(client_secret_path: str) -> str:
    return os.path.join(os.path.dirname(client_secret_path), "token.json")


def _load_credentials() -> Credentials:
    client_secret_path = os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    if not client_secret_path:
        raise RuntimeError("GOOGLE_CLIENT_SECRET_PATH environment variable is not set")

    token_path = _token_path(client_secret_path)
    creds = None
    if os.path.exists(token_path):
        # No `scopes` argument here on purpose: this token file is shared with
        # other projects on the same Google account, and passing a narrower
        # scope list overrides (and would overwrite on refresh) whatever
        # broader scope set is already recorded -- silently shrinking what
        # the file grants for everyone else using it.
        creds = Credentials.from_authorized_user_file(token_path)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def build_gmail_service() -> Resource:
    return build("gmail", "v1", credentials=_load_credentials())
