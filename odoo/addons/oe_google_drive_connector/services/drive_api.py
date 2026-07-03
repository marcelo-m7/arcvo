# -*- coding: utf-8 -*-
"""Thin, self-contained wrapper around the official Google Drive v3 client.

This layer is deliberately independent of the Odoo ORM apart from accepting a
``gdrive.connection`` record so it can read credentials and persist refreshed
OAuth tokens. It is shared verbatim across Odoo 17/18/19.

Two credential strategies are supported:
  * ``oauth``           - authorization-code flow with an offline refresh token
  * ``service_account`` - server-to-server JSON key, optional user impersonation
"""

import io
import json
import logging
import os

_logger = logging.getLogger(__name__)

# Google often returns more scopes than requested (e.g. when the user already
# granted others); without this, oauthlib raises "Scope has changed" on exchange.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

# The official Google libraries are optional at import time so the module can be
# installed before the dependencies are present; a clear error is raised the
# moment a connection is actually used.
try:
    from google.oauth2.credentials import Credentials as UserCredentials
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as TokenRequest
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build as build_drive
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import GoogleAuthError

    GOOGLE_LIBS = True
    GOOGLE_IMPORT_ERROR = None
except (ImportError, IOError) as err:  # pragma: no cover - environment dependent
    GOOGLE_LIBS = False
    GOOGLE_IMPORT_ERROR = err
    HttpError = Exception  # so ``except HttpError`` stays valid without the lib
    GoogleAuthError = Exception  # base for RefreshError / delegation failures

# Full Drive access is required to create folders anywhere the user chooses and
# to work with Shared Drives. Kept as a single constant for easy auditing.
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
FOLDER_MIME = "application/vnd.google-apps.folder"

# Google-native document export targets when a binary download is impossible.
NATIVE_EXPORTS = {
    "application/vnd.google-apps.document":
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.google-apps.spreadsheet":
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation":
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.google-apps.drawing": "application/pdf",
}


class DriveError(Exception):
    """Raised for any Drive-side failure with a human-readable message."""


def libraries_available():
    return GOOGLE_LIBS


def missing_library_message():
    return (
        "The Python packages 'google-api-python-client', 'google-auth' and "
        "'google-auth-oauthlib' are required. Install them with: "
        "pip install google-api-python-client google-auth google-auth-oauthlib"
        " (underlying error: %s)" % GOOGLE_IMPORT_ERROR
    )


def _client_config(client_id, client_secret, redirect_uri):
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "redirect_uris": [redirect_uri],
        }
    }


def build_consent_url(client_id, client_secret, redirect_uri, state):
    """Return the Google consent-screen URL for the authorization-code flow."""
    if not GOOGLE_LIBS:
        raise DriveError(missing_library_message())
    flow = Flow.from_client_config(
        _client_config(client_id, client_secret, redirect_uri), scopes=DRIVE_SCOPES
    )
    flow.redirect_uri = redirect_uri
    # Disable PKCE: the authorization and token-exchange steps happen in two
    # separate HTTP requests, so the auto-generated code_verifier would be lost.
    # This is a confidential (client_secret) web app, so PKCE is not required.
    flow.autogenerate_code_verifier = False
    flow.code_verifier = None
    url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true",
        prompt="consent", state=state,
    )
    return url


def exchange_consent_code(client_id, client_secret, redirect_uri, code):
    """Trade the authorization code for credentials. Returns a plain dict."""
    if not GOOGLE_LIBS:
        raise DriveError(missing_library_message())
    flow = Flow.from_client_config(
        _client_config(client_id, client_secret, redirect_uri), scopes=DRIVE_SCOPES
    )
    flow.redirect_uri = redirect_uri
    flow.autogenerate_code_verifier = False
    flow.code_verifier = None
    try:
        flow.fetch_token(code=code)
    except Exception as exc:  # oauthlib / requests errors are not DriveError
        raise DriveError("Token exchange with Google failed: %s" % exc)
    creds = flow.credentials
    return {
        "refresh_token": creds.refresh_token,
        "access_token": creds.token,
        "token_expiry": creds.expiry,  # naive UTC datetime, ready for Odoo
    }


class DriveSession(object):
    """Stateful helper bound to one ``gdrive.connection`` record."""

    def __init__(self, connection):
        if not GOOGLE_LIBS:
            raise DriveError(missing_library_message())
        self.connection = connection
        self.shared_drive_id = connection.shared_drive_id or None
        self._service = None

    # -- credentials ----------------------------------------------------------
    def _oauth_credentials(self):
        conn = self.connection
        if not conn.refresh_token:
            raise DriveError(
                "This connection has no refresh token yet. Use 'Connect' to "
                "complete the Google authorization first."
            )
        creds = UserCredentials(
            token=conn.access_token or None,
            refresh_token=conn.refresh_token,
            token_uri=TOKEN_URI,
            client_id=conn.client_id,
            client_secret=conn.client_secret,
            scopes=DRIVE_SCOPES,
        )
        if not creds.valid:
            try:
                creds.refresh(TokenRequest())
            except GoogleAuthError as exc:
                raise DriveError(
                    "Could not refresh the Google token (it may be expired or "
                    "revoked). Reconnect this connection. Details: %s" % exc)
            # Persist the freshly minted access token so subsequent calls reuse it.
            conn.sudo().write({
                "access_token": creds.token,
                "token_expiry": creds.expiry,
            })
        return creds

    def _service_account_credentials(self):
        conn = self.connection
        try:
            info = json.loads(conn.service_account_key or "{}")
        except ValueError as exc:
            raise DriveError("The service account key is not valid JSON: %s" % exc)
        if not info:
            raise DriveError("No service account key was provided on this connection.")
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=DRIVE_SCOPES
        )
        if conn.impersonate_email:
            creds = creds.with_subject(conn.impersonate_email)
        return creds

    def _build(self):
        if self.connection.auth_method == "service_account":
            creds = self._service_account_credentials()
        else:
            creds = self._oauth_credentials()
        return build_drive("drive", "v3", credentials=creds, cache_discovery=False)

    @property
    def service(self):
        if self._service is None:
            self._service = self._build()
        return self._service

    # -- shared-drive aware request kwargs ------------------------------------
    def _drive_kwargs(self):
        if self.shared_drive_id:
            return {"supportsAllDrives": True}
        return {}

    def _list_kwargs(self):
        if self.shared_drive_id:
            return {
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
                "corpora": "drive",
                "driveId": self.shared_drive_id,
            }
        return {}

    # -- operations -----------------------------------------------------------
    def about(self):
        """Cheap call used to validate that credentials actually work."""
        try:
            return self.service.about().get(fields="user(emailAddress,displayName)").execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))

    def find_child_folder(self, name, parent_id):
        safe = name.replace("'", "\\'")
        query = (
            "mimeType = '%s' and trashed = false and '%s' in parents and name = '%s'"
            % (FOLDER_MIME, parent_id, safe)
        )
        try:
            resp = self.service.files().list(
                q=query, spaces="drive", fields="files(id,name,webViewLink)",
                pageSize=1, **self._list_kwargs()
            ).execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))
        files = resp.get("files") or []
        return files[0] if files else None

    def ensure_folder(self, name, parent_id):
        """Return an existing child folder of ``parent_id`` or create it."""
        existing = self.find_child_folder(name, parent_id)
        if existing:
            return existing
        body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
        try:
            return self.service.files().create(
                body=body, fields="id,name,webViewLink", **self._drive_kwargs()
            ).execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))

    def ensure_root(self, name):
        """Ensure the top-level folder. Parent is the Shared Drive or My Drive."""
        parent = self.shared_drive_id or "root"
        return self.ensure_folder(name, parent)

    def upload(self, parent_id, filename, mimetype, content):
        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype=mimetype or "application/octet-stream",
            resumable=True,
        )
        body = {"name": filename, "parents": [parent_id]}
        try:
            return self.service.files().create(
                body=body, media_body=media,
                fields="id,name,webViewLink,webContentLink", **self._drive_kwargs()
            ).execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))

    def update_content(self, file_id, mimetype, content):
        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype=mimetype or "application/octet-stream",
            resumable=True,
        )
        try:
            return self.service.files().update(
                fileId=file_id, media_body=media,
                fields="id,name,webViewLink", **self._drive_kwargs()
            ).execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))

    def download(self, file_id):
        """Return raw bytes; falls back to exporting Google-native documents."""
        try:
            meta = self.service.files().get(
                fileId=file_id, fields="mimeType", **self._drive_kwargs()
            ).execute()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))
        mime = meta.get("mimeType")
        buffer = io.BytesIO()
        try:
            if mime in NATIVE_EXPORTS:
                request = self.service.files().export_media(
                    fileId=file_id, mimeType=NATIVE_EXPORTS[mime]
                )
            else:
                request = self.service.files().get_media(
                    fileId=file_id, **self._drive_kwargs()
                )
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _status, done = downloader.next_chunk()
        except (HttpError, GoogleAuthError) as exc:
            raise DriveError(_describe_error(exc))
        return buffer.getvalue()

    def delete(self, file_id):
        try:
            self.service.files().delete(fileId=file_id, **self._drive_kwargs()).execute()
            return True
        except (HttpError, GoogleAuthError) as exc:
            # 404 means it is already gone - treat as success for idempotency.
            if getattr(exc, "resp", None) is not None and exc.resp.status == 404:
                return True
            raise DriveError(_describe_error(exc))


def _describe_error(exc):
    """Turn a Drive API HttpError or a google-auth error into a short string."""
    if not isinstance(exc, HttpError):
        # Auth/transport failures: RefreshError, unauthorized_client (delegation
        # not configured), invalid service-account key, expired/revoked token, etc.
        return "Google authentication error: %s" % exc
    try:
        payload = json.loads(exc.content.decode("utf-8"))
        message = payload.get("error", {}).get("message") or str(exc)
        status = getattr(exc, "resp", None) and exc.resp.status
        return "Google Drive API error %s: %s" % (status, message)
    except Exception:
        return str(exc)
