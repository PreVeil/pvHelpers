import types

from pvHelpers.logger import g_log
from pvHelpers.mail.email import EmailBase, PROTOCOL_VERSION
from pvHelpers.user import LocalUser, User
from pvHelpers.utils import CaseInsensitiveDict, params

from .prepared_message import (PreparedMessageV1, PreparedMessageV2,
                               PreparedMessageV3, PreparedMessageV4,
                               PreparedMessageV5, PreparedMessageV6)
from .prepared_message.helpers import PreparedMessageError


class PreparedMessageFactory(object):
    """ PreparedMessage factory class """

    @staticmethod
    @params(LocalUser, EmailBase, {User, CaseInsensitiveDict}, {int, types.NoneType})
    def new(sender, email, recipient, protocol_version=None):
        try:

            if protocol_version:
                prepared_msg_pv = protocol_version
            else:
                prepared_msg_pv = email.protocol_version

            if prepared_msg_pv == PROTOCOL_VERSION.V1:
                return True, PreparedMessageV1(sender, email, recipient)
            elif prepared_msg_pv == PROTOCOL_VERSION.V2:
                return True, PreparedMessageV2(sender, email, recipient)
            elif prepared_msg_pv == PROTOCOL_VERSION.V3:
                return True, PreparedMessageV3(sender, email, recipient)
            elif prepared_msg_pv == PROTOCOL_VERSION.V4:
                return True, PreparedMessageV4(sender, email, recipient)
            elif prepared_msg_pv == PROTOCOL_VERSION.V5:
                # recipient is a dict of recip_user_data for this version
                return True, PreparedMessageV5(sender, email, recipient)
            elif prepared_msg_pv == PROTOCOL_VERSION.V6:
                return True, PreparedMessageV6(sender, email, recipient)

        except PreparedMessageError as e:
            g_log.exception(e)
            return False, None

        g_log.error(
            u"PreparedMessageFactory.new: Unsupported protocol_version {}".format(prepared_msg_pv))
        return False, None
