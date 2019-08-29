from setuptools import Command
import re


class Version(Command):
    """
    This class allows Buildbot to dynamically get the version number specified
    in `setup.py` so that it can reference the appropriate corresponding artifact
    name in order to upload it to the S3 bucket.
    """

    description = "Get the version number specified in setup.py"
    user_options = [] # required by CmdClass - empty for our purposes

    def initialize_options(self):
        """This method must be implemented - blank for our purposes"""
        pass

    def finalize_options(self):
        """This method must be implemented - blank for our purposes"""
        pass

    def run(self):
        """Use regex on `setup.py` to extract the version number string for BuildBot"""
        pattern = re.compile('version\s*=\s*\"(.*)\"', re.MULTILINE)
        file_path = 'version.py'
        with open(file_path, 'r') as setup:
            version = re.search(pattern, setup.read()).group(1)
        return version
