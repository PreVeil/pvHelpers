from pvHelpers.utils import b64enc, jdumps


class User(object):
    def claim_account(self, user_id, secret, key_version):
        resp = self.put(
            u"{}/put/account/{}".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps({"secret" : secret, "key_version": key_version})
        )
        resp.raise_for_status()
        return resp.json()

    def freeAsyncQueue(self):
        resp = self.put(
            "{}/free_async_queue".format(self.url),
             headers=self.__headers__,
            timeout=10 # endpoint can halt
        )
        resp.raise_for_status()

    def inviteUser(self, inviter, invitee):
        resp = self.post(
            u"{}/user/{}/invite".format(self.url, inviter), headers=self.__headers__,
            raw_body=jdumps({"invitee": invitee})
        )
        resp.raise_for_status()
        return resp.json()

    def deleteUser(self, user_ids):
        resp = self.delete(
            u"{}/users".format(self.url), headers=self.__headers__,
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def list_local_users(self, user_ids=[]):
        resp = self.put(
            u"{}/get/account/list/local".format(self.url), headers=self.__headers__,
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def update_and_list_local_users(self, as_user, user_ids=[]):
        resp = self.put(
            u"{}/get/users/{}/localusers".format(self.url, as_user), headers=self.__headers__,
            raw_body=jdumps({"user_ids": user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def encryptTextForUser(self, user_id, for_user_id, plaintext):
        resp = self.put(
            u"{}/post/{}/encrypt".format(self.url, user_id), headers=self.__headers__,
             raw_body=jdumps({
                "encrypt_for": for_user_id,
                "plaintext": b64enc(plaintext)
             })
        )
        resp.raise_for_status()
        return resp.json()

    def decryptTextForExportMember(self, user_id, member_id, member_kv, export_id, cipher):
        resp = self.put(
            "{}/get/users/{}/exports/{}/decrypt".format(self.url, user_id, export_id), headers=self.__headers__,
             raw_body=jdumps({
                "for_user_id": member_id,
                "for_user_key_version": member_kv,
                "ciphertext": b64enc(cipher)
             })
        )
        resp.raise_for_status()
        return resp.json()

    def fetchMIMEForExport(self, user_id, member_id, member_kv, export_id, member_collection_id, message_id, message_version):
        resp = self.put(
            "{}/get/users/{}/exports/{}/message".format(self.url, user_id, export_id), headers=self.__headers__,
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

    def startExport(self, user_id, org_id, export_id, dropdir):
        resp = self.put(
            "{}/put/users/{}/orgs/{}/exportself/{}/start".format(self.url, user_id, org_id, export_id),
                headers=self.__headers__,
             raw_body=jdumps({"dropdir": dropdir,})
        )
        resp.raise_for_status()
        return resp.json()

    def deleteExport(self, user_id, org_id, export_id):
        resp = self.put(
            "{}/delete/users/{}/orgs/{}/exportself/{}".format(self.url, user_id, org_id, export_id),
                headers=self.__headers__,
        )
        resp.raise_for_status()
        return resp.json()

    def cancelExport(self, user_id, org_id, export_id):
        resp = self.put(
            "{}/put/users/{}/orgs/{}/exportself/{}/cancel".format(self.url, user_id, org_id, export_id),
                headers=self.__headers__,
        )
        resp.raise_for_status()
        return resp.json()

    def rekeyUserKey(self, user_id, trigger_update=True):
        resp = self.put(
            "{}/put/users/{}/key".format(self.url, user_id), headers=self.__headers__,
        )
        resp.raise_for_status()
        # only way client would know to replace the `temp`(new) key is if
        # it gets 498 from server some random server request should trigger it
        if trigger_update:
            self.listUserDevices(user_id)
        return resp.json()

    def getRemoteUsersInfo(self, as_user_id, for_user_ids):
        resp = self.put(
            "{}/get/account/{}".format(self.url, as_user_id), headers=self.__headers__,
             raw_body=jdumps({"user_ids": for_user_ids})
        )
        resp.raise_for_status()
        return resp.json()

    def reconstructUser(self, user_id, secret):
        resp = self.put(
            u"{}/post/account/{}/key/reconstruct".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({"secret": secret})
        )
        resp.raise_for_status()
        return resp.json()

    def setApprovalGroup(self, user_id, required_users, optional_users, optionals_required):
        resp = self.put(
            u"{}/post/users/{}/approval/users".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({
                "required_users": required_users, "optional_users": optional_users,
                "optionals_required": optionals_required,
            })
        )
        resp.raise_for_status()
        return resp.json()

    # This resources triggers a rekey as well
    def changeApprovalGroup(self, user_id, required_users, optional_users, optionals_required):
        resp = self.put(
            u"{}/put/users/{}/approval/users".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({
                "required_users": required_users, "optional_users": optional_users,
                "optionals_required": optionals_required,
            })
        )
        resp.raise_for_status()
        return resp.json()

    def getUserself(self, user_id, status=u"pending", hide_expired=True, limit=50, offset=0):
        resp = self.put(
            u"{}/get/users/{}/self".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({
                "status": status, "hide_expired": hide_expired,
                "limit": limit, "offset": offset,
            })
        )
        resp.raise_for_status()
        return resp.json()

    def getUserApprovalGroup(self, user_id):
        resp = self.put(u"{}/get/users/{}/approval/users".format(self.url, user_id),
            raw_body=None, headers=self.__headers__
        )
        resp.raise_for_status()
        return resp.json()

    def getUserApprovals(self, user_id, status=u"pending", response=u"pending", hide_expired=True, limit=50, offset=0):
        resp = self.put(
            u"{}/get/users/{}/approvals".format(self.url, user_id), headers=self.__headers__,
            raw_body=jdumps({"response": response, "status": status, "hide_expired": hide_expired, "offset": offset, "limit": limit})
        )
        resp.raise_for_status()
        return resp.json()

    def respondToUserApproval(self, user_id, request_id, request_payload, response):
        resp = self.put(
            u"{}/put/users/{}/approvals/{}".format(self.url, user_id, request_id), headers=self.__headers__,
            raw_body=jdumps({"request": request_payload, "response": response})
        )
        resp.raise_for_status()
        return resp.json()

    def getUserRequestResponses(self, user_id, request_id):
        resp = self.put(
            u"{}/get/users/{}/self/{}/responses".format(self.url, user_id, request_id),
            headers=self.__headers__,
        )
        resp.raise_for_status()
        return resp.json()

    def subsumeUserAccount(self, admin_id, org_id, subsumed_user_id, dept_name):
        resp = self.put(
            u"{}/post/users/{}/orgs/{}/subsume".format(self.url, admin_id, org_id),
            headers=self.__headers__,
            raw_body=jdumps({"subsume_user_id": subsumed_user_id, "department": dept_name})
        )
        resp.raise_for_status()
        return resp.json()
