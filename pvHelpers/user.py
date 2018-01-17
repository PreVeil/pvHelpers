import requests, types
from . import keys
from . import misc
from . import apiclient
from .luser_info import LUserInfo

class OrganizationInfo(object):
    def __init__(self, organiztion_id, organiztion_name, department_name, role):
        self.org_id = organiztion_id
        self.org_name = organiztion_name
        self.dept_name = department_name
        self.role = role

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.toDict() == other.toDict()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def toDict(self):
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "dept_name": self.dept_name,
            "role": self.role
        }

# Model for User Bucket protocol_version=1
class UserDBNode(object):
    @staticmethod
    def new(user_id, display_name, mail_cid, password, org_info, luser_info):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(display_name, unicode):
            return False, None
        if not isinstance(mail_cid, unicode):
            return False, None
        if not isinstance(password, unicode):
            return False, None
        if not isinstance(org_info, (types.NoneType, OrganizationInfo)):
            return False, None
        if not isinstance(luser_info, (LUserInfo, misc.NOT_ASSIGNED)):
            return False, None

        return True, UserDBNode(user_id, display_name, mail_cid, password, org_info, luser_info)

    def __init__(self, user_id, display_name, mail_cid, password, org_info, luser_info):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.password = password
        self.org_info = org_info
        self.luser_info = luser_info

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "password" : self.password,
            "org_info" : self.org_info if self.org_info is None else self.org_info.toDict(),
            "luser_info" : str(self.luser_info)
        }

class UserData(object):
    def __init__(self, user_id, display_name, mail_cid, public_key, organiztion_info):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.public_key = public_key
        self.org_info = organiztion_info

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "org_info" : self.org_info if self.org_info is None else self.org_info.toDict()
        }
    def isClaimed(self):
        return self.public_key is not None

def fetchUser(user_id, client, key_version=-1):
    if not isinstance(user_id, unicode):
        return False, None
    if not isinstance(key_version, (int, long)):
        return False, None

    status, user_data = fetchUsers([(user_id, key_version)], client)
    if status == False:
        return False, None
    if len(user_data) != 1:
        return False, None
    if user_id not in user_data:
        return False, None
    user_datum = user_data[user_id]
    if user_datum == False:
        return False, None
    return True, user_datum

def _materializeUserDatum(json_user, client):
    user_id = json_user.get("user_id")
    if user_id == None:
        return False, None

    display_name = json_user.get("display_name")
    if display_name == None:
        return False, None

    mail_cid = json_user.get("mail_collection_id")
    if mail_cid == None:
        return False, None

    org_id = json_user.get("entity_id")
    org_meta = json_user.get("entity_metadata")
    organiztion_info = None
    if isinstance(org_id, unicode) and isinstance(org_meta, dict):
        department = org_meta.get("department")
        role = org_meta.get("role")
        status, org_info = getOrgInfo(org_id, client)
        if status is False:
            org_name = None
        else:
            org_name = org_info.get("display_name")

        organiztion_info = OrganizationInfo(org_id, org_name, department, role)

    public_key = json_user.get("public_key")
    if public_key:
        status, public_key = keys.PublicKey.deserialize(user_id, misc.jdumps(public_key))
        if status == False:
            return False, None

    return True, UserData(user_id, display_name, mail_cid, public_key, organiztion_info)

# You probably want to use fetchUsers().
def _fetchUsers(queries, client):
    if not isinstance(client, apiclient.UserAPIClient):
        return False, None
    params = {"spec" : misc.jdumps(queries)}
    try:
        resp = client.get("/users", params=params)
        if resp.status_code != requests.codes.ok:
            return False, None
    except requests.exceptions.RequestException as e:
        return False, None

    text = resp.text
    if resp.encoding != "utf-8" or not isinstance(text, unicode):
        return False, None
    status, data = misc.jloads(text)
    if status == False:
        return False, None

    return True, data

def fetchUsers(user_ids, client):
    if not isinstance(user_ids, list):
        return False, None
    query_data = []
    for x in user_ids:
        if len(x) != 2:
            return False, None
        query_data.append({"user_id": x[0], "key_version": x[1]})

    status, query_result = _fetchUsers(query_data, client)
    if status == False:
        return False, None
    users = query_result.get("users")
    if users == None:
        return False, None

    output = misc.CaseInsensitiveDict()
    for u in users:
        status, user_datum = _materializeUserDatum(u, client)
        if status == False:
            continue
        output[user_datum.user_id] = user_datum

    return True, output

def getOrgInfo(org_id, client):
    try:
        resp = client.get("/users/orgs/{}".format(org_id))
    except requests.exceptions.RequestException as e:
        g_log.error("getOrgInfo: request exception: %s" % e)
        return False, None

    if resp.status_code != requests.codes.ok:
        g_log.error("getOrgInfo: bad status code: %s" % resp.status_code)
        return False, None

    if resp.encoding != "utf-8" or not isinstance(resp.text, unicode):
        g_log.error("getOrgInfo: bad encoding")
        return False, None

    status, data = misc.jloads(resp.text)
    if status == False:
        g_log.error("getOrgInfo: invalid json response")
        return False, None

    return True, data
