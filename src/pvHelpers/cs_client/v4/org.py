from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class OrgV4(object):
    @params(object, LocalUser, unicode)
    def get_org_info(self, user, org_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}".format(org_id), "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, {int, long})
    def getOrgAdminChanges(self, user, org_id, since_rev_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/admins".format(org_id), "GET", None
        )
        resp = self.get(url, headers, raw_body, params={u"since_rev_id" : since_rev_id})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, object)
    def createOrg(self, user, params):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs", "POST", params
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode, {int, long}, object)
    def createOrgAG(self, user, org_id, name, optionals_required, approvers):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/groups".format(org_id), "POST", {
                u"name": name,
                u"optionals_required": optionals_required,
                u"approvers": approvers
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def deleteOrgAG(self, user, org_id, group_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/groups/{}".format(org_id, group_id), "DELETE", None
        )
        resp = self.delete(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, object)
    def updateOrg(self, user, org_id, params):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}".format(org_id), "PATCH", params
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, list)
    def addOrgMembers(self, user, org_id, new_members):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/members".format(org_id), "POST", {
                u"users" : new_members
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode)
    def getOrgAGs(self, user, org_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/groups".format(org_id), "GET", None
        )
        resp = self.get(url, headers, raw_body, params={u"since_rev_id" : -1})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode, unicode, unicode)
    def updateOrgMemberDepartment(self, user, org_id, member_id, role, department):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/members".format(org_id), "PATCH",{
                u"user_id"    : member_id,
                u"role"       : role, # role is set to latest role from caller
                u"department" : department
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
