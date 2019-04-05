import sys
from setuptools import setup, find_packages

install_requires = [
    "PyYAML==3.11", "requests==2.20.1", "simplejson==3.8.2",
    "SQLAlchemy==1.1.5.dev0", "Werkzeug==0.14.1", "libnacl==1.4.5+preveil1",
    "flanker==0.4.40+preveil1.10", "pysqlite==2.8.3.1", "semver==2.7.7",
    "protobuf==3.5.2.post1", "fipscrypto==1.0"
]

if sys.platform == "win32":
    install_requires += ["pywin32==224"]

setup(
    name="pvHelpers",
    version="4.62",
    packages=find_packages(),
    install_requires=install_requires,
)
