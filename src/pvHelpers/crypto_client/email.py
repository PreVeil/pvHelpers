from pvHelpers.mail.email import EmailHelpers
from pvHelpers.utils import b64enc, jdumps, NotAssigned


class EmailFetch(object):
    def fetch_emails_with_content(self, user_id, server_ids, inlines_only=False):
        resp = self.put(
            u"{}/mail/thread/{}".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({"unique_ids": server_ids, "inlines_only": False})
        )
        resp.raise_for_status()
        emails_with_content = resp.json()
        assert set(server_ids) == set(emails_with_content["messages"].keys())
        return emails_with_content["messages"]

    def fetch_paginated_threads(self, user_id, mailbox_id, limit, offset):
        self.doUpdate([user_id])
        resp = self.put(
            u"{}/mail/{}".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps([{"id": mailbox_id, "offset": offset, "limit": limit}])
        )
        resp.raise_for_status()
        mailbox_update = resp.json()
        assert mailbox_id in mailbox_update
        return mailbox_update[mailbox_id]

    def copy_emails(self, user_id, src_mid, dest_mid, server_ids, trash_src):
        resp = self.put(
            u"{}/post/account/{}/copy".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps({
                "email_ids": server_ids, "src_mailbox_id": src_mid,
                "dest_mailbox_id": dest_mid, "trash_source": trash_src
            })
        )
        resp.raise_for_status()
        data = resp.json()
        assert all([id_ in data.keys() for id_ in server_ids])
        if trash_src:
            assert all("email_update" in i for i in data.values())
        self.doUpdate([user_id])
        return data


class EmailSend(object):
    def delete_email(self, user_id, server_id):
        resp = self.put(
            u"{}/delete/account/{}/emails/".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps({"emails": [server_id]})
        )
        resp.raise_for_status()
        data = resp.json()
        assert server_id in data.keys()
        self.doUpdate([user_id])
        return data

    def send_smtp_email(self, protocol_version, sender_id, tos, raw_msg):
        resp = self.put(
            u"{}/put/account/{}/message/smtp".format(self.url, sender_id), headers=self.__headers__,
            raw_body=jdumps({"tos": tos, "raw_msg": b64enc(raw_msg), "protocol_version": protocol_version})
        )
        resp.raise_for_status()
        self.doUpdate([sender_id] + tos)
        return resp.json()

    def append_imap_email(self, protocol_version, user_id, mailbox_id, flags, raw_msg):
        resp = self.put(
            u"{}/put/account/{}/message/imap".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps({
                "mailbox_id":  mailbox_id,
                "flags": flags, "raw_msg": b64enc(raw_msg), "protocol_version": protocol_version
            })
        )
        resp.raise_for_status()
        self.doUpdate([user_id])
        return resp.json()

    def send_email(self, protocol_version, sender, tos, ccs, bccs,
                   subject, text, html, attachments, in_reply_to, references,
                   reply_tos=[], flags=[], server_attr=NotAssigned(), message_id=None):
        # send attachments as multipart form-encode
        resp = self.put(
            u"{}/put/account/{}/message".format(self.url, sender["user_id"]), {},
            files=[("attachments", (file_.filename, file_, file_.content_type)) for file_ in attachments], raw_body={
                "json": jdumps({
                    "subject": subject,
                    "sender": sender,
                    "tos": tos,
                    "ccs": ccs,
                    "bccs": bccs,
                    "text": text,
                    "html": html,
                    "in_reply_to": in_reply_to,
                    "references": references,
                    "reply_tos": reply_tos,
                    "protocol_version": protocol_version,
                    "attachments": [{
                        "filename": file_.filename,
                        "content_type": file_.content_type,
                        "content_disposition": "attachment",
                        "content_id": u"<{}>".format(EmailHelpers.new_message_id()),
                        "blob_reference": file_.filename
                    } for file_ in attachments]
                })
            }
        )
        resp.raise_for_status()
        return resp.json()
