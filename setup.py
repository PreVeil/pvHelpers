from distutils.core import setup
setup(name="pvHelpers",
      version="1.90",
      packages=["pvHelpers", "pvHelpers.email", "pvHelpers.crypto", "pvHelpers.crypto.asymm_key",
                "pvHelpers.crypto.box", "pvHelpers.crypto.user_key", "pvHelpers.crypto.sign_key",
                "pvHelpers.crypto.symm_key"],
      install_requires=[
        "PyYAML==3.11",
        "requests==2.7.0",
        "simplejson==3.8.2",
        "SQLAlchemy==1.1.5.dev0",
        "Werkzeug==0.11.4",
        "libnacl==1.4.5+preveil1",
        "flanker==0.4.40",
        "pysqlite==2.8.3",
        "semver==2.7.7"
      ],
)
