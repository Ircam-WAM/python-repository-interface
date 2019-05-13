
from .component import Interface


class IRepository(Interface):

    """Common repository interface"""

    def __init__(self, url, settings={}, debug=False):
        """Allocate internal resources and reset state, so that this repository is
        ready for a new run.
        """

    @staticmethod
    def id():
        """Short alphanumeric, lower-case string which uniquely identify this
        repository, suitable for use as an HTTP/GET argument value, in filenames,
        etc..."""

        # implementation: only letters and digits are allowed. An exception will
        # be raised by MetaRepository if the id is malformed or not unique amongst
        # registered repositories.

    @staticmethod
    def name():
        """Name of the repository with any character"""

    def get_repository_instance(self):
        # Vendor instance to act on the repository
        """ """

    def get_host_instance(self):
        # Vendor instance to act on the host
        """" """

    def get_readme(self):
        """ """

    def get_summary(self):
        """ """

    def get_latest_commits(self):
        """ """

    def get_latest_tags(self):
        """ """

    def get_archive_url(self, **kwargs):
        """ """

    def get_commits_contributors(self):
        """ """

    def get_issues_contributors(self):
        """ """

    def get_members(self):
        """ """

    def get_languages(self):
        """ """
