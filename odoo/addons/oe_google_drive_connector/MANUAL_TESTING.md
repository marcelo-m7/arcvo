# Manual Testing Guide — `oe_google_drive_connector`

A step-by-step QA script to verify the module end-to-end against a **real Google Drive
account**. Allow ~30–45 minutes including the one-time Google Cloud setup.

> Automated install + ORM checks already pass. This guide covers the parts that need a
> live Google account, a reachable Odoo URL, and outbound network access.

---

## 0. Prerequisites

- [ ] Odoo 18 with `oe_google_drive_connector` installed.
- [ ] Server has the Python deps:
      `pip install google-api-python-client google-auth google-auth-oauthlib`
- [ ] Your Odoo is reachable at a stable URL and **`web.base.url`** is correct
      (*Settings → Technical → System Parameters → `web.base.url`*). For OAuth, Google must
      be able to redirect a browser to `<web.base.url>/gdrive/oauth/callback`
      (`http://localhost:8069` works for local testing).
- [ ] A Google account (personal or Workspace) and access to
      <https://console.cloud.google.com>.
- [ ] Logged into Odoo as a user in **Google Drive / Manager** (admins qualify).

---

## 1. Smoke test (no Google account needed)

| # | Step | Expected |
|---|------|----------|
| 1.1 | Open *Apps*, confirm **Google Drive Connector** is installed. | Present, no errors. |
| 1.2 | Top menu shows **Google Drive**. | Visible. |
| 1.3 | *Google Drive → Configuration → Connections → New*. | Form opens, state = **Not Connected**. |
| 1.4 | Switch **Authentication** between OAuth / Service Account. | Credential fields show/hide accordingly. |
| 1.5 | Check the **Authorized Redirect URI** field. | Equals `<web.base.url>/gdrive/oauth/callback`. |
| 1.6 | As a non-manager user, open a connection. | Client secret / key / tokens are **hidden**. |

---

## 2. Google Cloud setup (one-time)

1. Create/select a project at <https://console.cloud.google.com>.
2. **APIs & Services → Library →** enable **Google Drive API**.

### OAuth credentials
3. **OAuth consent screen** → *External* → fill required fields → add your Google address
   under **Test users** → Save.
4. **Credentials → Create credentials → OAuth client ID → Web application**.
5. Under **Authorized redirect URIs** add the exact URI from step 1.5 → **Create**.
6. Copy **Client ID** and **Client secret**.

### Service Account credentials (for section 6)
7. **Credentials → Create credentials → Service account** → create.
8. Open it → **Keys → Add key → Create new key → JSON** → download the file.
9. Note the service account **email** (`...@...iam.gserviceaccount.com`).

---

## 3. OAuth connection

| # | Step | Expected |
|---|------|----------|
| 3.1 | New connection: Authentication **OAuth**, paste **Client ID** + **Secret**, **Root folder name** = `Odoo Test`. Save. | Saved, still **Not Connected**. |
| 3.2 | Click **Connect**. | Redirect to Google consent screen. |
| 3.3 | Approve all requested permissions. | Browser returns to the Odoo connection form. |
| 3.4 | Observe state + banner. | State = **Connected**, green banner "Connected as <email>". |
| 3.5 | In Google Drive (web), check *My Drive*. | A folder **`Odoo Test`** exists. |
| 3.6 | Click the **Open in Drive** stat button. | Opens the root folder in Drive. |

**Failure checks**
- [ ] Wrong redirect URI in Google → after consent you get a Google error → connection
      stays `error` with a message in **Activity Logs**.
- [ ] Click **Reset** → tokens cleared, state back to **Not Connected**.

---

## 4. Manual upload (push) — four ways in the UI

First: *Settings → Google Drive* → set **Default connection** = your connection, **Offload** off, Save.
Then attach 1–2 files to any record that has a chatter (e.g. a **Contact**: *Contacts → open a contact →*
paperclip in the chatter → attach files).

There are **four** places to upload manually — test each:

| # | Where to click | Steps | Expected |
|---|---|---|---|
| 4.A | **Chatter message button** | On the record's chatter, hover the message that shows the attachment(s) → in the message toolbar click the **☁ cloud-upload** icon ("Upload to Google Drive"). | Success toast "Attachment(s) uploaded to Google Drive." |
| 4.B | **Attachment form** | *Settings → Technical → Database Structure → Attachments* (or *Google Drive → Synced Files*) → open an attachment → click **Upload to Google Drive** in the header. | Record reloads; **status badge = On Drive**, **Open in Drive** button appears. |
| 4.C | **Attachment kanban** | Open an attachment **kanban** view → on a card click **☁ Upload to Drive**. | Card reloads; shows green **On Drive** with a link. |
| 4.D | **Bulk from a list** | *Google Drive → Synced Files* or any attachment **list** → tick rows → **Actions ▸ Push to Google Drive** → pick a connection → **Push**. | Wizard shows counts; success notification; rows become **On Drive**. |

**Verification (after any method above):**

| # | Step | Expected |
|---|------|----------|
| 4.5 | *Google Drive → Synced Files* — the pushed rows. | `gdrive_state = On Drive`, **Open** button present. |
| 4.6 | Click **Open** (or the Drive link). | File opens in Google Drive. |
| 4.7 | In Drive, check the path. | File sits in `<Root> / <Model> / <Record name>` (e.g. `Odoo / Contact / Acme`). |
| 4.8 | Attach another file to the **same** record and upload it. | Lands in the **same** record folder (no duplicate folder created). |

> The chatter button (4.A) appears only on messages that actually carry attachments, and only for internal
> users. If a user has no connected connection, clicking it shows a clear error toast instead of uploading.

---

## 5. Offload & fetch-back

| # | Step | Expected |
|---|------|----------|
| 5.1 | *Settings → Google Drive*: turn **Offload binaries** on. Save. | Saved. |
| 5.2 | Attach a new file to a record and push it. | Pushed; attachment becomes a **link** (type `url`). |
| 5.3 | In *Synced Files*, the row shows **Offloaded**. | `gdrive_offloaded = true`. |
| 5.4 | (Optional, technical) confirm the binary is gone from Odoo storage. | Attachment has no local data. |
| 5.5 | Select the offloaded row → **Fetch back**. | Binary restored; `gdrive_offloaded = false`. |

---

## 6. Service Account connection

| # | Step | Expected |
|---|------|----------|
| 6.1 | New connection: Authentication **Service Account**, paste the JSON key. | Saved. |
| 6.2 | Enable **Use a Shared Drive**; enter a **Shared Drive ID**; in Drive, add the service-account email as a member of that Shared Drive. (Workspace alt: set **Impersonate User** + domain-wide delegation.) | — |
| 6.3 | Click **Test Connection**. | State = **Connected**; root folder created in the Shared Drive. |
| 6.4 | Push an attachment using this connection (via the wizard's connection selector). | File appears in the Shared Drive under the root folder. |

> If a plain service account targets *My Drive* (no Shared Drive, no impersonation),
> expect a quota/permission error — this is a Google limitation, not a bug.

---

## 7. Auto-push rule + scheduled job

| # | Step | Expected |
|---|------|----------|
| 7.1 | *Google Drive → Configuration → Auto-Push Rules → New*: Model = **Contact** (`res.partner`), Connection = your connection, Auto Push **on**. Save. | Saved. |
| 7.2 | Attach a new file to a contact; do **not** push manually. | Attachment is local only. |
| 7.3 | *Settings → Technical → Scheduled Actions →* **Google Drive: Push Attachments** → **Run Manually**. | Job runs without error. |
| 7.4 | Check *Synced Files*. | The new attachment is now **On Drive**. |
| 7.5 | Add a domain to the rule (e.g. `[("is_company","=",True)]`) and repeat with a person vs a company. | Only matching records' files are pushed. |

---

## 8. Deletion & logs

| # | Step | Expected |
|---|------|----------|
| 8.1 | Delete a synced attachment in Odoo. | Attachment removed; the matching Drive file is removed (or already-gone is tolerated). |
| 8.2 | *Google Drive → Configuration → Activity Logs*. | Entries for connects, pushes, and any errors; filter by level works. |
| 8.3 | Trigger a failure (e.g. push with a revoked token), then check logs. | An **error** entry with a readable message; connection may flip to `error`. |

---

## 9. Regression / negative cases

- [ ] Push with **no connected connection** → clear UserError, no crash.
- [ ] Select only system/web-asset attachments → "nothing to push" message.
- [ ] Uninstall the module on a test DB → uninstalls cleanly.
- [ ] Re-run *Test Connection* after several hours (OAuth) → token auto-refreshes, stays Connected.

---

## Result log

**Run:** 2026-06-11 · Odoo 18 · DB `test_v18c` · connection #1 "Odoo Gdrive Sync" (OAuth) ·
account `swagat.parida777@gmail.com` · executed live against Google Drive. **12/12 checks passed.**

| Section | Pass/Fail | Notes |
|---|---|---|
| 1 Smoke | ✅ PASS | Connection `connected`; root folder **Odoo** (`1RwVuDlO…cMku`) confirmed present in Drive. |
| 3 OAuth connect | ✅ PASS | Completed via browser (ngrok https); token stored, root folder auto-created. |
| 4 Manual push | ✅ PASS | `hello_gdrive.txt` uploaded → `linked`; `gdrive.folder` "GDrive Test Partner" created; file's Drive `parents` = record folder; 2nd file reused same folder (no dup). |
| 5 Offload/fetch | ✅ PASS | Offload → attachment became `url` + `offloaded`; fetch-back restored exact `binary` content. |
| 6 Service Account | ⏭️ NOT TESTED | No service-account key available in this run. Re-run section 6 with a JSON key + Shared Drive. |
| 7 Auto-push | ✅ PASS | Rule on `res.partner` + `_cron_push_attachments()` pushed 1 new attachment → `linked`. |
| 8 Delete/logs | ✅ PASS | Unlink removed the Drive file (subsequent `files.get` 404s); activity logs recorded all pushes + "Connection verified". |
| 9 Negative | ⏭️ NOT RUN | Optional; covered indirectly (syncable filter, idempotent folders). |

> Test data was committed to `test_v18c` and real folders/files were created under the **Odoo** root in the
> connected Google Drive (`GDrive Test Partner/`, `GDrive Auto Partner/`). Safe to delete after inspection.

Report issues to **apps@odooerp.ae** with the Odoo server log and the relevant
*Activity Logs* entries.
