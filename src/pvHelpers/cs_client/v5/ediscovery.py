from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class EDiscoveryV5(object):
    def getExportMessage(self, user, export_id, collection_id, member_id, id, version=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/mail/{}/messages/{}".format(collection_id, id),
            "GET", None, export=(export_id, member_id)
        )
        resp = self.get(url, headers, params={"version": version})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def getEDiscoveryShards(self, user, org_id, export_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/export/{}/group/shards".format(org_id),
            "GET", None
        )
        resp = self.get(url, headers, params={"request_id": export_id})
        resp.raise_for_status()
        return resp.json()

    def submitExportShards(self, user, org_id, shards, group_id, group_version):
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

    # deprecated
    def makeEDiscReq(self, user, org_id, until, users):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/export/{}/request".format(org_id),
            "POST", {
                "until": until,
                "users": users,
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    # deprecated
    def approveEDiscReq(self, user, org_id, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/export/{}/request/{}/approve".format(org_id, request_id),
            "POST", None
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    # deprecated
    def getEDiscReq(self, user, org_id, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/export/{}/request/{}".format(org_id, request_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
