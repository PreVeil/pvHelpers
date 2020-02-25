import sys

from setuptools import find_packages, setup

install_requires = [
    "PyYAML==5.3", "requests==2.20.1", "simplejson==3.8.2",
    "SQLAlchemy==1.1.5.dev0", "Werkzeug==0.14.1", "libnacl==1.4.5+preveil2",
    "flanker==0.4.40+preveil1.10", "pysqlite==2.8.3.1", "semver==2.7.7",
    "protobuf==3.5.2.post1", "pacparser==1.3.7", "fipscrypto==1.1.0",
    "sssa-python==0.0.2"
]

if sys.platform == "win32":
    install_requires += ["pywin32==220", "wincertstore==0.2"]


setup(
    name="pvHelpers",
    version="6.0.15",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=("tests")),
    install_requires=install_requires,
)
