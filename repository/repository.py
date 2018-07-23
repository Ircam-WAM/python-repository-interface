from .vendors import *

class Repository:

    url = None
    vendor = None
    vendor_client = None
    vendor_instance = None
    debug = False

    # Supported vendors
    vendors = [
        ('gitlab', gitlab.GitlabRepository),
        #('github', github.GithubRepository)
    ]

    def __init__(self, url, vendor, settings={}, debug=False):

        self.url = url
        self.vendor = vendor
        self.debug = debug

        for (v, i) in self.vendors:
            if v == self.vendor:
                self.vendor_client = i
                self.vendor_instance = self.vendor_client(self.url,
                                                          settings=settings,
                                                          debug=self.debug)

        if not self.vendor_client:
            raise Exception("Repository vendor is not supported")

    def get_instance(self):
        return self.vendor_instance.get_instance()

    def get_readme(self):
        return self.vendor_instance.get_readme()

    def get_summary(self):
        return self.vendor_instance.get_summary()

    def get_latest_commits(self):
        return self.vendor_instance.get_latest_commits()

    def get_latest_tags(self):
        return self.vendor_instance.get_latest_tags()

    def get_archive_url(self, **kwargs):
        return self.vendor_instance.get_archive_url(**kwargs)

    def get_commits_contributors(self):
        return self.vendor_instance.get_commits_contributors()

    def get_issues_contributors(self):
        return self.vendor_instance.get_issues_contributors()

    def get_members(self):
        return self.vendor_instance.get_members()
