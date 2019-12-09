from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class ExportV5(object):
    @params(object, LocalUser, {int, long}, unicode, unicode, unicode)
    def get_mail_history_for_export(self, user, last_rev_id, for_user_id, for_user_cid, export_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes".format(for_user_cid),
            "GET", None, False, (export_id, for_user_id)
        )
        resp = self.get(url, headers, raw_body, params={
            "since_rev_id": last_rev_id,
        })
        resp.raise_for_status()
        return resp.json()

    def get_export_mail(self, user, export_id, collection_id, member_id, id, version=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/mail/{}/messages/{}".format(collection_id, id),
            "GET", None, export=(export_id, member_id)
        )
        resp = self.get(url, headers, params={"version": version})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def get_export_shards(self, user, org_id, export_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/export/{}/group/shards".format(org_id),
            "GET", None
        )
        resp = self.get(url, headers, params={"request_id": export_id})
        resp.raise_for_status()
        return resp.json()

    def submit_export_shards(self, user, org_id, shards, group_id, group_version):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/submit_export_shards".format(org_id),
            "POST", {
                "user_id": user.user_id,
                "shards": shards,
                "group_id": group_id,
                "group_version": group_version
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
