import requests

from . import misc

class UserData:
    def __init__(self, email, user_id, display_name, mail_cid):
        self.email        = email
        self.user_id      = user_id
        self.display_name = display_name
        self.mail_cid     = mail_cid

def fetchUserByEmail(email, backend, key_version=-1):
    if not isinstance(email, unicode):
        return False, None
    if not isinstance(key_version, (int, long)):
        return False, None

    status, user_data = fetchUsersByEmail([(email, key_version)], backend)
    if status == False:
        return False, None
    if len(user_data) != 1:
        return False, None
    if email not in user_data:
        return False, None
    user_datum = user_data[email]
    if user_datum == False:
        return False, None
    return True, user_datum

def fetchUserByID(user_id, backend, key_version=-1):
    if not isinstance(user_id, (int, long)):
        return False, None
    if not isinstance(key_version, (int, long)):
        return False, None

    status, user_data = fetchUsersByID([(user_id, key_version)], backend)
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

def _materializeUserDatum(json_user):
    user_email = json_user.get("email")
    if user_email == None:
        return False, None

    user_id = json_user.get("user_id")
    if user_id == None:
        return False, None
    status, user_id = misc.toInt(user_id)
    if status == False:
        return False, None

    display_name = json_user.get("display_name")
    if display_name == None:
        return False, None

    mail_cid = json_user.get("mail_collection_id")
    if mail_cid == None:
        return False, None

    return True, UserData(user_email, user_id, display_name, mail_cid)

# You probably don't want to call this function directly.  Use the
# fetchUsersBy* interfaces.
def _fetchUsers(queries, backend):
    url = backend + "/users"
    params = {"spec" : misc.jdumps(queries)}

    try:
        resp = requests.get(url, params=params, timeout=misc.HTTP_TIMEOUT,
                allow_redirects=False)
        if resp.status_code != requests.codes.ok:
            return False, None
    except requests.exceptions.RequestException as e:
        return False, None

    text = resp.text
    if resp.encoding != 'utf-8' or not isinstance(text, unicode):
        return False, None
    status, data = misc.jloads(text)
    if status == False:
        return False, None

    return True, data

def fetchUsersByEmail(emails, backend):
    if not isinstance(emails, list):
        return False, None
    for x in emails:
        if len(x) != 2:
            return False, None

    query_data = [{"email" : e[0], "key_version" : e[1]} for e in emails]
    status, query_result = _fetchUsers(query_data, backend)
    if status == False:
        return False, None
    users = query_result.get("users")
    if users == None:
        return False, None

    output = misc.CaseInsensitiveDict()
    for u in users:
        status, user_datum = _materializeUserDatum(u)
        if status == False:
            continue
        output[user_datum.email] = user_datum

    for (e, _) in emails:
        if e not in output:
            output[e] = False

    return True, output

def fetchUsersByID(ids, backend):
    if not isinstance(ids, list):
        return False, None
    for x in ids:
        if len(x) != 2:
            return False, None

    query_data = [{"user_id" : i[0], "key_version" : i[1]} for i in ids]
    status, query_result = _fetchUsers(query_data, backend)
    if status == False:
        return False, None
    users = query_result.get("users", None)
    if users == None:
        return False, None

    output = {}
    for u in users:
        status, user_datum = _materializeUserDatum(u)
        if status == False:
            continue
        output[user_datum.user_id] = user_datum

    for (i, _) in ids:
        if i not in output:
            output[i] = False

    return True, output
