from pvHelpers.utils import jdumps, utf8_encode

class Mailbox(object):
    def createMailbox(self, user_id, name):
        resp = self.put(
            u"{}/create/mailbox/{}".format(self.url, user_id), headers=self.__headers__,
            raw_body=utf8_encode(jdumps({"mailbox_name": name}))
        )
        resp.raise_for_status()
        data = resp.json()
        assert len(data) == 1
        m = data.values()[0]
        self.doUpdate([user_id])
        return m["server_id"]

    def deleteMailbox(self, user_id, server_id):
        resp = self.put(
            u"{}/delete/mailbox/{}".format(self.url, user_id), headers=self.__headers__,
            raw_body=utf8_encode(jdumps({"mailbox_id": server_id}))
        )
        resp.raise_for_status()
        return resp.json()

    def renameMailbox(self, user_id, server_id, new_name):
        resp = self.put(
            u"{}/rename/mailbox/{}".format(self.url, user_id), headers=self.__headers__,
            raw_body=utf8_encode(jdumps({"mailbox_new_name": new_name, "mailbox_id": server_id}))
        )
        resp.raise_for_status()
        return resp.json()