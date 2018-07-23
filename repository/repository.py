from .vendors import *


class Repository:

    url = None
    vendor = None
    vendor_client = None
    #vendor_instance = None

    # Supported vendors
    vendors = [
        ('gitlab', gitlab.GitlabRepository),
        #('github', github.GithubRepository)
    ]

    def __init__(self, url, vendor):

        self.url = url
        self.vendor = vendor

        for (v, i) in self.vendors:
            if v == self.vendor:
                self.vendor_client = i

        if not self.vendor_client:
            raise Exception("Repository vendor is not supported")

    def get_instance(self):
        return self.vendor_client(self.url).get_instance()

    def get_readme(self):
        return self.vendor_client(self.url).get_readme()

    def get_summary(self):
        return self.vendor_client(self.url).get_summary()

    def get_latest_commits(self):
        return self.vendor_client(self.url).get_latest_commits()

    def get_latest_tags(self):
        return self.vendor_client(self.url).get_latest_tags()

    def get_archive_url(self, **kwargs):
        return self.vendor_client(self.url).get_archive_url(**kwargs)

    def get_commits_contributors(self):
        return self.vendor_client(self.url).get_commits_contributors()

    def get_issues_contributors(self):
        return self.vendor_client(self.url).get_issues_contributors()

    def get_members(self):
        return self.vendor_client(self.url).get_members()
