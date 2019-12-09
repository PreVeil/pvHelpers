from pvHelpers.utils import jdumps


class Test(object):
    def create_test_account(self, user_id, name, for_luser_info=None):
        resp = self.put(
            u"{}/put/test/account/{}".format(self.url, user_id),
            self.__headers__,
            raw_body=jdumps({"name": name, "for_luser_info": for_luser_info})
        )
        resp.raise_for_status()
        return resp.json()
