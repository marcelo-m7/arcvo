# Google Drive Connector (`oe_google_drive_connector`)

Connect Odoo to Google Drive: every business record gets its own Drive folder, and
attachments are pushed to Drive as shareable links — with an optional one-way
scheduled sync and the choice between OAuth or a Service Account.

* **Author:** Oakland.ae · **Website:** https://odooerp.ae · **Support:** apps@odooerp.ae
* **License:** OPL-1
* **Odoo:** 19.0 (`19.0.1.0.0`) — shares its core with the 17.0 and 18.0 builds.

---

## What it does

| Capability | Detail |
|---|---|
| Connect Google Drive | OAuth user-consent **or** Service Account (per connection). Multiple connections supported. |
| Per-record folders | Files are filed under `Root / <Model> / <Record>` in Drive, created on demand. |
| Push attachments | One-click push of any `ir.attachment` to the record's Drive folder; the file becomes a Drive link. |
| Storage offload | Optionally drop the binary from Odoo after upload (attachment becomes a `url` link) to keep the database light. |
| Fetch back | Re-download an offloaded file's binary into Odoo at any time. |
| Auto-push (optional) | Per-model rules + a scheduled job push new attachments to Drive automatically (one-way, Odoo → Drive). |
| Shared Drives | Target a Shared (Team) Drive instead of *My Drive*. |
| Activity log | Searchable log of pushes and connection events, with automatic retention trim. |

This module is intentionally **lightweight and Google-Drive-only**. It does *not*
implement bidirectional/reverse sync, a queue engine, or a custom file-manager UI.

---

## Requirements

Python packages on the Odoo server:

```bash
pip install google-api-python-client google-auth google-auth-oauthlib
```

Odoo dependencies: `base`, `mail`, `web` (all standard).

---

## Installation

1. Install the Python packages above into the Odoo environment/venv.
2. Copy `oe_google_drive_connector` into your addons path.
3. *Apps → Update Apps List*, then install **Google Drive Connector**.

---

## Configuration

### A. Google Cloud project (once)

1. Go to <https://console.cloud.google.com>, create or select a project.
2. **APIs & Services → Library →** enable **Google Drive API**.
3. Pick an authentication method below.

### B. OAuth (user consent)

1. In Odoo: *Google Drive → Configuration → Connections → New*, set **Authentication = OAuth**.
2. Copy the **Authorized Redirect URI** shown on the form
   (`https://<your-odoo>/gdrive/oauth/callback`).
3. In Google Cloud: **OAuth consent screen** → *External* → fill app info → add your
   account under **Test users** (or *Publish* the app — see note).
4. **Credentials → Create credentials → OAuth client ID → Web application** → add the
   redirect URI from step 2 → copy **Client ID** and **Client secret**.
5. Paste them into the connection, set a **Root folder name** (e.g. `Odoo`), **Save**,
   then click **Connect** and approve in Google.

> **Note:** while the OAuth app is in *Testing* mode, Google expires the refresh token
> after 7 days. *Publish* the app on the consent screen for a stable connection.

### C. Service Account (server-to-server)

1. **Credentials → Create credentials → Service account →** create a **JSON key** and
   download it.
2. In Odoo set **Authentication = Service Account** and paste the full JSON key.
3. Give the service account access to where files should live:
   * **Recommended:** enable **Use a Shared Drive**, enter the Shared Drive ID, and add
     the service-account email as a member of that Shared Drive; **or**
   * For Google Workspace, set **Impersonate User** and configure domain-wide delegation
     for the service account (scope `https://www.googleapis.com/auth/drive`).
4. Click **Test Connection**.

> **Important:** a bare service account has no usable *My Drive* storage quota. For
> Service Account connections, target a **Shared Drive** or use **impersonation**.

### D. Settings

*Settings → Google Drive*:

* **Default connection** — used by the manual *Push to Google Drive* action.
* **Offload binaries to Drive** — when on, pushed files leave Odoo and become links.
* **Log retention (days)** — daily clean-up of the activity log.

---

## Usage

### Manual push
Open any record (or *Google Drive → Synced Files*), select attachments, and use the
**Actions → Push to Google Drive** menu. Choose a connection and confirm. Files appear
in `Root / <Model> / <Record>` in Drive and show an **Open** link in Odoo.

### Automatic push
*Google Drive → Configuration → Auto-Push Rules → New*: pick a model (e.g. `sale.order`),
an optional record filter (domain), and a connection. Enable the cron **Google Drive:
Push Attachments** (*Settings → Technical → Scheduled Actions*, off by default).

### Offloaded files
With offload enabled, a pushed attachment becomes a Drive link. Use **Fetch back** on the
*Synced Files* list to restore the binary into Odoo.

---

## Security

| Group | Can |
|---|---|
| **Google Drive / User** | Push attachments, open Drive links, view synced files. |
| **Google Drive / Manager** | Everything above + manage connections, rules, logs, settings. |

System administrators are Managers automatically. Credential secrets (client secret,
tokens, service-account key) are restricted to Managers at the field level. Push runs
with elevated rights only to read credentials; record visibility still follows normal
Odoo access rules.

---

## Architecture (short)

* `services/drive_api.py` — a self-contained wrapper over the official Google Drive v3
  SDK (`googleapiclient` + `google-auth`). Version-agnostic; shared across 17/18/19.
* `gdrive.connection` — one Drive connection (auth, tokens, root/Shared-Drive target, state).
* `gdrive.folder` — a **flat** pointer mapping one Odoo record to its Drive folder
  (no recursive tree).
* `gdrive.mapping` — optional per-model auto-push rule.
* `gdrive.log` — minimal activity log.
* `ir.attachment` — extended with `gdrive_file_id`, `gdrive_url`, `gdrive_state`,
  `gdrive_offloaded`, `gdrive_connection_id` and push/fetch/offload methods.
* `controllers/oauth.py` — the `/gdrive/oauth/callback` endpoint (resolves the connection
  via the OAuth `state` parameter).

---

## Limitations

* Sync is **one-way** (Odoo → Drive). Files created directly in Drive are not imported.
* Google-native documents (Docs/Sheets/Slides) are exported to Office/PDF on *fetch back*.
* No real-time sync; auto-push runs on the scheduled job.

---

## Support

Questions or issues: **apps@odooerp.ae**.
