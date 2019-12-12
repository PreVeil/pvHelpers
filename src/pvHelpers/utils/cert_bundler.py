class CertBundler(object):
    def __init__(self, path):
        # this import will generate a cert bundle that includes both os and certifi.
        # it also patches certifi.where() to point to the path of the newly expanded cert bundle.
        from certifi_win32.wrapt_certifi import apply_patches  # noqa: F401

        self.path = path

    def generate_bundle(self):
        pass
