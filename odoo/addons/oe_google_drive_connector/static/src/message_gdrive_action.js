/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registerMessageAction } from "@mail/core/common/message_actions";

/**
 * Adds a "Upload to Google Drive" action to the hover toolbar of any chatter
 * message that carries one or more attachments. Odoo 19 uses the destructured
 * message-action API (registerMessageAction, name/onSelected).
 */
registerMessageAction("gdrive_upload", {
    condition: ({ message, store }) =>
        message.attachment_ids.length && store.self.main_user_id?.share === false,
    icon: "fa fa-cloud-upload",
    name: _t("Upload to Google Drive"),
    onSelected: async ({ message, owner }) => {
        const ids = message.attachment_ids.map((rec) => rec.id);
        const { orm, notification } = owner.env.services;
        try {
            await orm.call("ir.attachment", "action_gdrive_push", [ids]);
            notification.add(_t("Attachment(s) uploaded to Google Drive."), {
                type: "success",
            });
        } catch (error) {
            const msg =
                (error && error.data && error.data.message) ||
                (error && error.message) ||
                _t("Upload to Google Drive failed.");
            notification.add(msg, { type: "danger" });
        }
    },
    // Low sequence so it shows as an inline quick action, not hidden in the "..." menu.
    sequence: 1,
});
