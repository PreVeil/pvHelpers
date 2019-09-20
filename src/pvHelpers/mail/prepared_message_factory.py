import pvHelpers as H

from .prepared_message import (PreparedMessageBase, PreparedMessageError,
                               PreparedMessageV1, PreparedMessageV2,
                               PreparedMessageV3, PreparedMessageV4)


#########################################
####### Prepared Message Factory ########
#########################################
class PreparedMessageFactory(object):
    @staticmethod
    def new(sender, email, recipient):
        try:
            if email.protocol_version == H.PROTOCOL_VERSION.V1:
                return True, PreparedMessageV1(sender, email, recipient)
            elif email.protocol_version == H.PROTOCOL_VERSION.V2:
                return True, PreparedMessageV2(sender, email, recipient)
            elif email.protocol_version == H.PROTOCOL_VERSION.V3:
                return True, PreparedMessageV3(sender, email, recipient)
            elif email.protocol_version == H.PROTOCOL_VERSION.V4:
                return True, PreparedMessageV4(sender, email, recipient)

        except PreparedMessageError as e:
            g_log.exception(e)
            return False, None

        H.g_log.error(u"PreparedMessageFactory.new: Unsupported protocol_version")
        return False, None
