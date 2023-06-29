import abc, sys
from . import misc
from pvHelpers import EncodingException
if sys.platform in ["win32"]:
    from .win_helpers import PySID, ws, ADMINISTRATORS_SID, LOCAL_SYSTEM_SID


class LUserInfo(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, platform):
        self.platform = platform

    @staticmethod
    def new(platform, luser_info):
        if platform == "win32":
            (sid, psids) = luser_info
            if not isinstance(sid, PySID):
                raise TypeError(u"sid must be of type PySID")
            if not isinstance(psids, list):
                raise TypeError(u"psids must be of type list")
                for psid in psids:
                    if not isinstance(psid, PySID):
                        raise TypeError(u"psid must be of type PySID")

            return LUserInfoWin(sid, psids)

        elif platform == "darwin":
            if not isinstance(luser_info, int):
                raise TypeError(u"luser_info/uid must be of type int")

            return LUserInfoUnix(luser_info)

        elif platform == "linux2":
            if not isinstance(luser_info, int):
                raise TypeError(u"luser_info/uid must be of type int")

            return LUserInfoLinux(luser_info)

        else:
            raise ValueError("{} is unsupported platform".format(platform))

    # Temp helper to unpack user_store value
    @staticmethod
    def deserialize(json_str):
        if json_str == str(misc.NOT_ASSIGNED()):
            return misc.NOT_ASSIGNED()
        try:
            _dict = misc.jloads(json_str)
        except EncodingException as e:
            raise ValueError(e)

        platform = _dict["platform"]
        if platform == "win32":
            return LUserInfoWin.deserialize(_dict)
        elif platform == "darwin":
            return LUserInfoUnix.deserialize(_dict)
        elif platform == "linux2":
            return LUserInfoLinux.deserialize(_dict)
        else:
            raise ValueError("{} is unsupported platform".format(platform))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.serialize()

    @abc.abstractmethod
    def serialize(self):
        raise NotImplementedError()

    # Not supported in Python 2.7 :/
    # Make sure subclasses have the classmethod
    # @abc.abstractclassmethod
    # def deserialize(cls, _dict):
    #     raise NotImplementedError()

    @abc.abstractmethod
    def isAdmin(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def isPreVeil(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __eq__(self, other):
        raise NotImplementedError()

    def __ne__(self, other):
        return not self.__eq__(other)

class LUserInfoWin(LUserInfo):
    platform = "win32"
    def __init__(self, sid, psids):
        self.sid = sid
        self.psids = psids
        super(LUserInfoWin, self).__init__(LUserInfoWin.platform)

    @classmethod
    def deserialize(cls, _dict):
        platform = _dict["platform"]
        if platform != cls.platform:
            raise ValueError("platform must be {}".format(cls.platform))
        sid = ws.ConvertStringSidToSid(_dict["info"]["sid"])
        psids = [ws.ConvertStringSidToSid(spsid) for spsid in _dict["info"]["psids"]]
        return cls(sid, psids)

    def serialize(self):
        ssid = ws.ConvertSidToStringSid(self.sid)
        spsids = [ws.ConvertSidToStringSid(psid) for psid in self.psids]

        return misc.jdumps({
            "platform": self.platform,
            "info": {
                "sid": ssid,
                "psids": spsids
            }
        })

    def isAdmin(self):
        return ADMINISTRATORS_SID in self.psids

    def isPreVeil(self):
        # currently our services run as LocalSystem
        # TODO: create preveil group in windows
        return LOCAL_SYSTEM_SID == self.sid

    def __eq__(self, other):
        return self.sid == other.sid

class LUserInfoUnix(LUserInfo):
    platform = "darwin"

    @classmethod
    def deserialize(cls, _dict):
        platform = _dict["platform"]
        if platform != cls.platform:
            raise ValueError("platform must be {}".format(cls.platform))
        suid = _dict["info"]["uid"]
        status, uid = misc.toInt(suid)
        if status == False:
            raise ValueError("uid int coercion failed: {}".format(suid))

        return cls(uid)


    def __init__(self, uid):
        self.uid = uid
        super(LUserInfoUnix, self).__init__(LUserInfoUnix.platform)

    def serialize(self):
        return misc.jdumps({
            "platform": self.platform,
            "info": {
                "uid": self.uid
            }
        })

    def isAdmin(self):
        # root considered Admin
        # TODO: check if user's group info if is part of `root` group
        return self.uid == 0 or self.uid == 501  # TODO:PX56: UNHACK 501

    def isPreVeil(self):
        import pwd
        PREVEIL_UID = pwd.getpwnam("preveil").pw_uid

        return PREVEIL_UID == self.uid

    def __eq__(self, other):
        return self.uid == other.uid

class LUserInfoLinux(LUserInfo):
    platform = "linux2"

    @classmethod
    def deserialize(cls, _dict):
        platform = _dict["platform"]
        if platform != cls.platform:
            raise ValueError("platform must be {}".format(cls.platform))
        suid = _dict["info"]["uid"]
        status, uid = misc.toInt(suid)
        if status == False:
            raise ValueError("uid int coercion failed: {}".format(suid))

        return cls(uid)

    def __init__(self, uid):
        self.uid = uid
        super(LUserInfoLinux, self).__init__(LUserInfoLinux.platform)

    def serialize(self):
        return misc.jdumps({
            "platform": self.platform,
            "info": {
                "uid": self.uid
            }
        })

    def isAdmin(self):
        # root considered Admin
        # TODO: check if user's group info if is part of `root` group
        return self.uid == 0

    def isPreVeil(self):
        import pwd
        PREVEIL_UID = pwd.getpwnam("preveil").pw_uid

        return PREVEIL_UID == self.uid

    def __eq__(self, other):
        return self.uid == other.uid
