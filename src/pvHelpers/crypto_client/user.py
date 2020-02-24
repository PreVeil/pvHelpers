from pvHelpers.utils import jdumps


class User(object):
    def claim_account(self, user_id, secret, key_version):
        resp = self.put(
            u"{}/put/account/{}".format(self.url, user_id),
            raw_body=jdumps({"secret": secret, "key_version": key_version})
        )
        resp.raise_for_status()
        return resp.json()

    def free_async_queue(self):
        resp = self.put(
            "{}/free_async_queue".format(self.url),
            timeout=10  # endpoint can halt
        )
        resp.raise_for_status()

    def invite_user(self, inviter, invitee):
        resp = self.post(
            u"{}/user/{}/invite".format(self.url, inviter),
            raw_body=jdumps({"invitee": invitee})
        )
        resp.raise_for_status()
        return resp.json()

    def delete_user(self, user_ids):
        resp = self.delete(
            u"{}/users".format(self.url),
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def list_local_users(self, user_ids=[]):
        resp = self.put(
            u"{}/get/account/list/local".format(self.url),
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def update_and_list_local_users(self, as_user, user_ids=[]):
        resp = self.put(
            u"{}/get/users/{}/localusers".format(self.url, as_user),
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def get_export_mime(self, user_id, member_id, member_kv, export_id,
                        member_collection_id, message_id, message_version):
        resp = self.put(
            "{}/get/users/{}/exports/{}/message".format(self.url, user_id, export_id),
            raw_body=jdumps({
                "collection_id": member_collection_id,
                "for_user_id": member_id,
                "for_user_key_version": member_kv,
                "id": message_id,
                "version": message_version
             })
        )
        resp.raise_for_status()
        return resp.json()

    def start_export(self, user_id, org_id, export_id, dropdir):
        resp = self.put(
            "{}/put/users/{}/orgs/{}/exportself/{}/start".format(self.url, user_id, org_id, export_id),
            raw_body=jdumps({"dropdir": dropdir})
        )
        resp.raise_for_status()
        return resp.json()

    def delete_export(self, user_id, org_id, export_id):
        resp = self.put("{}/delete/users/{}/orgs/{}/exportself/{}".format(self.url, user_id, org_id, export_id))
        resp.raise_for_status()
        return resp.json()

    def cancel_export(self, user_id, org_id, export_id):
        resp = self.put("{}/put/users/{}/orgs/{}/exportself/{}/cancel".format(self.url, user_id, org_id, export_id))
        resp.raise_for_status()
        return resp.json()

    def rekey_user_key(self, user_id, trigger_update=True):
        resp = self.put(
            "{}/put/users/{}/key".format(self.url, user_id),
        )
        resp.raise_for_status()
        # only way client would know to replace the `temp`(new) key is if
        # it gets 498 from server some random server request should trigger it
        if trigger_update:
            self.listUserDevices(user_id)
        return resp.json()

    def get_remote_users_info(self, as_user_id, for_user_ids):
        resp = self.put(
            "{}/get/account/{}".format(self.url, as_user_id),
            raw_body=jdumps({"user_ids": for_user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def reconstruct_user(self, user_id, secret):
        resp = self.put(
            u"{}/post/account/{}/key/reconstruct".format(self.url, user_id),
            raw_body=jdumps({"secret": secret})
        )
        resp.raise_for_status()
        return resp.json()

    def set_user_approval_group(self, user_id, required_users, optional_users, optionals_required):
        resp = self.put(
            u"{}/post/users/{}/approval/users".format(self.url, user_id),
            raw_body=jdumps({
                "required_users": required_users, "optional_users": optional_users,
                "optionals_required": optionals_required,
            })
        )
        resp.raise_for_status()
        return resp.json()

    def change_user_approval_group(self, user_id, required_users, optional_users, optionals_required):
        resp = self.put(
            u"{}/put/users/{}/approval/users".format(self.url, user_id),
            raw_body=jdumps({
                "required_users": required_users, "optional_users": optional_users,
                "optionals_required": optionals_required,
            })
        )
        resp.raise_for_status()
        return resp.json()

    def get_user_approval_group(self, user_id):
        resp = self.put(u"{}/get/users/{}/approval/users".format(self.url, user_id), raw_body=None)
        resp.raise_for_status()
        return resp.json()

    def get_user_approvals(self, user_id, status=u"pending",
                           response=u"pending", hide_expired=True, limit=50, offset=0):
        resp = self.put(
            u"{}/get/users/{}/approvals".format(self.url, user_id),
            raw_body=jdumps({
                "response": response,
                "status": status,
                "hide_expired": hide_expired,
                "offset": offset,
                "limit": limit
            }))
        resp.raise_for_status()
        return resp.json()

    def respond_to_user_approval(self, user_id, request_id, request_payload, response):
        resp = self.put(
            u"{}/put/users/{}/approvals/{}".format(self.url, user_id, request_id),
            raw_body=jdumps({"request": request_payload, "response": response})
        )
        resp.raise_for_status()
        return resp.json()

    def get_user_request_responses(self, user_id, request_id):
        resp = self.put(u"{}/get/users/{}/self/{}/responses".format(self.url, user_id, request_id))
        resp.raise_for_status()
        return resp.json()

    def subsume_user_account(self, admin_id, org_id, subsumed_user_id, dept_name):
        resp = self.put(
            u"{}/post/users/{}/orgs/{}/subsume".format(self.url, admin_id, org_id),
            raw_body=jdumps({"subsume_user_id": subsumed_user_id, "department": dept_name})
        )
        resp.raise_for_status()
        return resp.json()

    def handle_user_event(self, user_id, event_id, requester_id, requester_key_version, signature, payload):
        resp = self.put(
            u"{}/put/crypto/user/{}/event/{}".format(self.url, user_id, event_id),
            raw_body=jdumps({
                "requester_id": requester_id,
                "requester_key_version": requester_key_version,
                "signature": signature,
                "payload": payload
            }))
        resp.raise_for_status()
        return resp.json()