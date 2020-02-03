from pvHelpers.utils import jdumps, merge_dicts, rand_unicode


class Organization(object):
    def get_org_info(self, user_id, org_id):
        resp = self.put(
            u"{}/get/{}/orgs/{}".format(self.url, user_id, org_id),
        )
        resp.raise_for_status()
        return resp.json()

    def change_member_role(self, admin_id, org_id, member_id, role):
        resp = self.put(
            u"{}/put/users/{}/orgs/{}/members/{}".format(self.url, admin_id, org_id, member_id),
            raw_body=jdumps({"role": role})
        )
        resp.raise_for_status()
        return resp.json()

    def delete_org_member(self, admin_id, org_id, member_id):
        resp = self.put(u"{}/delete/users/{}/orgs/{}/members/{}".format(self.url, admin_id, org_id, member_id))
        resp.raise_for_status()
        return resp.json()

    def update_org_member_metadata(self, admin_id, org_id, member_id, department):
        resp = self.put(
            u"{}/put/{}/orgs/{}/members".format(self.url, admin_id, org_id, member_id),
            raw_body=jdumps({
                u"department": department,
                u"member_id": member_id
            })
        )
        resp.raise_for_status()
        return resp.json()

    def create_organization(self, user_id, org_name=None, department_name=None):
        if org_name is None:
            org_name = rand_unicode(5)
        if department_name is None:
            department_name = rand_unicode(5)
        resp = self.put(
            u"{}/post/account/{}/orgs".format(self.url, user_id),
            raw_body=jdumps({"org_name": org_name, "user_department": department_name})
        )
        resp.raise_for_status()
        data = resp.json()
        org_id = data.get("org_id")
        assert org_id is not None
        return data

    def invite_org_member(self, user_id, org_id, member_id, member_name, member_department_name, member_role):
        resp = self.put(
            u"{}/post/{}/orgs/{}/members".format(self.url, user_id, org_id),
            raw_body=jdumps({"users": [{
                "user_id": member_id, "display_name": member_name,
                "department": member_department_name, "role": member_role
            }]})
        )
        resp.raise_for_status()
        return resp.json()

    def create_org_approval_group(self, user_id, org_id, group_name, approvers, optionals_required):
        resp = self.put(
            u"{}/post/{}/orgs/{}/groups".format(self.url, user_id, org_id),
            raw_body=jdumps({
                "name": group_name, "optionals_required": optionals_required,
                "approvers": map(lambda a: {
                    "user_id": a['user_id'],
                    "account_version": 0,  # this needs fixing!
                    "required": False
                }, approvers)
            })
        )
        resp.raise_for_status()
        return resp.json()

    def get_org_approval_groups(self, user_id, org_id):
        resp = self.put(
            u"{}/get/{}/orgs/{}/groups".format(self.url, user_id, org_id),
        )
        resp.raise_for_status()
        return resp.json()

    def delete_org_approval_group(self, user_id, org_id, group_id):
        resp = self.put(
            u"{}/delete/{}/orgs/{}/groups/{}".format(self.url, user_id, org_id, group_id),
        )
        resp.raise_for_status()
        return resp.json()

    def set_roled_approval_group(self, user_id, org_id, group_id, group_version, group_role):
        resp = self.put(
            u"{}/put/{}/orgs/{}/groups/{}".format(self.url, user_id, org_id, group_id),
            raw_body=jdumps({"group_version": group_version, "group_role": group_role})
        )
        resp.raise_for_status()
        return resp.json()

    def set_members_approval_group(self, user_id, org_id, group_id, group_version,
                                   approvers, members, current_group_id=None, current_group_version=None):
        resp = self.put(
            u"{}/post/{}/orgs/{}/groups/{}/members".format(self.url, user_id, org_id, group_id),
            raw_body=jdumps(merge_dicts(approvers, {
                u"users": map(lambda u: u.user_id, members), "group_version": group_version,
                "current_group_id": current_group_id, "current_group_version": current_group_version
            }))
        )
        resp.raise_for_status()
        return resp.json()

    def respond_to_org_approval(self, user_id, org_id, request_id, request_payload, response):
        resp = self.put(
            u"{}/put/users/{}/orgs/{}/approvals/{}".format(self.url, user_id, org_id, request_id),
            raw_body=jdumps({"request": request_payload, "response": response})
        )
        resp.raise_for_status()
        return resp.json()

    def get_org_requests(self, user_id, org_id, status=u"pending", hide_expired=True, limit=50, offset=0):
        resp = self.put(
            u"{}/get/users/{}/orgs/{}/requests".format(self.url, user_id, org_id),
            raw_body=jdumps({"status": status, "hide_expired": hide_expired, "limit": limit, "offset": offset})
        )
        resp.raise_for_status()
        return resp.json()

    def delete_org_request(self, user_id, org_id, request_id):
        resp = self.put(
            u"{}/delete/users/{}/orgs/{}/requests/{}".format(self.url, user_id, org_id, request_id),
            headers=self.__headers__)
        resp.raise_for_status()
        return resp.json()

    def create_export_request(self, user_id, org_id, required_users):
        resp = self.put(
            u"{}/post/users/{}/orgs/{}/exportrequests".format(self.url, user_id, org_id),
            raw_body=jdumps({"users": required_users})
        )
        resp.raise_for_status()
        return resp.json()

    def get_local_export_requests(self, user_id):
        resp = self.put(u"{}/get/users/{}/exportrequests".format(self.url, user_id))
        resp.raise_for_status()
        return resp.json()
