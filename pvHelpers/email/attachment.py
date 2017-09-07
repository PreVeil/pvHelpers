from ..misc import ASCIIToUnicode, unicodeIfUnicodeElseDecode, g_log, encodeContentIfUnicode
import email_helpers
import content as cnt
from flanker import mime, addresslib
import types, copy

class AttachmentType(object):
    INLINE = u"inline"
    ATTACHMENT = u"attachment"

class AttachmentMetadata(object):
    __initialized = False
    def __init__(self, filename=None, content_type=None, content_disposition=AttachmentType.ATTACHMENT, content_id=None):
        if isinstance(filename, str):
            status, filename = ASCIIToUnicode(filename)
            if status == False:
                raise email_helpers.EmailException(u"AttachmentMetadata.__init__: failed to convert filename to unicode")
        if not isinstance(filename, (unicode, types.NoneType)):
            raise email_helpers.EmailException(u"AttachmentMetadata.__init__: filename must be unicode, {}".format(filename))
        self.filename = filename

        if isinstance(content_type, str):
            status, content_type = ASCIIToUnicode(content_type)
            if status == False:
                raise email_helpers.EmailException(u"AttachmentMetadata.__init__: failed to convert content_type to unicode")
        if not isinstance(content_type, (unicode, types.NoneType)):
            raise email_helpers.EmailException(u"AttachmentMetadata.__init__:: content_type must be of type unicode, {}".format(content_type))

        if content_type is None:
            self.content_type = u"application/octet-stream"
        else:
            self.content_type = content_type

        # if we don't specify this, flanker will default to (c-d= attachment)  or (c-d=None) if no filename available
        # defaulting to attachment so that we always return the raw content regardless,
        # and keep it MIME consistent with object
        content_disposition = AttachmentType.ATTACHMENT if content_disposition is None else content_disposition
        if isinstance(content_disposition, str):
            status, content_disposition = ASCIIToUnicode(content_disposition)
            if status == False:
                raise email_helpers.EmailException(u"AttachmentMetadata.__init__: failed to convert content_disposition to unicode")
        if not isinstance(content_disposition, unicode):
            raise email_helpers.EmailException(u"AttachmentMetadata.__init__: content_disposition must be unicode, value: {}".format(content_disposition))
        self.content_disposition = content_disposition

        if isinstance(content_id, str):
            status, content_id = ASCIIToUnicode(content_id)
            if status == False:
                raise email_helpers.EmailException(u"AttachmentMetadata.__init__: failed to convert content_id to unicode")
        if not isinstance(content_id, (unicode, types.NoneType)):
            raise email_helpers.EmailException(u"AttachmentMetadata.__init__: content_id must be unicode, value: {}".format(content_id))
        self.content_id = content_id

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"AttachmentMetadata has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)

    def toDict(self):
        return {
            "filename" : self.filename,
            "content_type" : self.content_type,
            "content_disposition" : self.content_disposition,
            "content_id" : self.content_id
        }

class Attachment(object):
    __initialized = False
    @staticmethod
    def fromFileStorage(_file):
        content = _file.read()
        status, content = encodeContentIfUnicode(content)
        if status == False:
            raise email_helpers.EmailException(u"fromFileStorage: Failed to encode content")

        # flanker defaults the mime header to (application/octet-stream) if c-t not specified
        # it also makes some assumptions based on filename if c-t is (application/octet-stream)
        # so keeping our object consistent with the MIME which is going to be generated
        try:
            main, sub = mime.message.headers.parametrized.fix_content_type(_file.content_type, default=(u"application", u"octet-stream"))
            content_type = mime.message.part.adjust_content_type(mime.message.ContentType(main, sub),  content, _file.filename)
        except mime.MimeError as e:
            raise email_helpers.EmailException(u"fromFileStorage: flanker exception, value: {}".format(e))

        return Attachment(AttachmentMetadata(_file.filename, _file.content_type), cnt.Content(content, None, None))

    @staticmethod
    def fromDict(data):
        metadata = data.get("metadata")
        metadata = AttachmentMetadata(metadata.get("filename"), metadata.get("content_type"), metadata.get("content_disposition"), metadata.get("content_id"))

        return Attachment(metadata, cnt.Content(**data.get("content")))

    # should use Email.fromDict() unless certain about types
    def __init__(self, metadata, content):
        if not isinstance(content, cnt.Content):
            raise email_helpers.EmailException(u"__init__: Bad content, reference_id: {}".format(reference_id))
        self.content = content

        if not isinstance(metadata, AttachmentMetadata):
            raise email_helpers.EmailException(u"__init__: bad metadata, value: {}".format(metadata))
        self.metadata = metadata
        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"Attachment has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)

    def loadContent(self, content):
        self.content.content = content

    # This must only be used in an email that's protocol_version 1,
    # TODO: make attachment factory
    def toMime(self):
        if self.content.content is None:
            #TODO: pass fetcher handles to Content object, so the instance can lazily load the content
            raise email_helpers.EmailException(u"toMime: content must be loaded")
        try:
            part = mime.create.attachment(content_type=self.metadata.content_type, body=self.content.content, filename=self.metadata.filename, disposition=self.metadata.content_disposition)
            if self.metadata.content_id:
                part.headers["Content-Id"] = self.metadata.content_id
        except mime.EncodingError as e:
            raise email_helpers.EmailException(u"toMime: flanker exception, {}".format(e))
        return part

    def toDict(self):
        return {
            "content" : self.content.toDict(),
            "metadata" : self.metadata.toDict()
        }

    def isLoaded(self):
        return self.content.isLoaded()
