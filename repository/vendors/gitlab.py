from .utils import VendorInterface, VendorMixin
import gitlab
from urllib.parse import urlparse, urljoin
import pydash as dsh


class GitlabRepository(VendorInterface, VendorMixin):

    url = None
    host = None
    namespace = None
    host_instance = None
    repository_instance = None
    settings = None

    def __init__(self, url, settings={}, **kwargs):

        self.url = url
        self.settings = settings
        debug_mode = kwargs['debug'] if 'debug' in kwargs else False
        parsed_url = urlparse(self.url)

        # Testing HTTPS
        # TODO: handle SSH as well (with public key kwarg)
        if not debug_mode:
            if parsed_url.scheme != 'https':
                raise Exception("Repository must use HTTPS")

        self.host = parsed_url.scheme + '://' + parsed_url.netloc
        self.namespace = parsed_url.path[1:]  # Stripping the first slash

        self.host_instance = gitlab.Gitlab(self.host, private_token=self.settings['API_TOKEN'])
        self.repository_instance = self.host_instance.projects.get(self.namespace)
        # TODO: test if host is indeed a Gitlab server

    def _get_user(self, username=None):
        # Gets the Gitlab user tied to a username.
        # Used mostly to get the email.
        user = self.host_instance.users.list(username=username)
        user = user[0]
        return user

    def get_host_instance(self):
        return self.host_instance

    def get_repository_instance(self):
        return self.repository_instance

    def get_readme(self):

        project = self.repository_instance

        def find_func(path):
            f = project.files.get(file_path=path, ref='master')
            return f.decode().decode("utf-8")

        path, html_content = super()._find_readme(find_func, readme_tests=self.settings['README_TESTS'])

        return (path, html_content)

    def get_summary(self):

        summary = {
            'latest_commits': self.get_latest_commits(),
            'latest_tags': self.get_latest_tags()
        }

        return summary

    def get_latest_commits(self):
        latest_commits = []
        project = self.repository_instance
        commits = project.commits.list()

        if len(commits) < self.settings['LATEST_COMMITS_LIMIT']:
            limit = len(commits)
        else:
            limit = self.settings['LATEST_COMMITS_LIMIT']

        for commit in commits[:limit]:
            c = commit.attributes
            commit_rel_url = self.settings['GITLAB_URL_COMMIT'].format(namespace=self.namespace,
                                                               sha=c['id'])
            commit_abs_url = '{0}{1}'.format(self.settings['GITLAB_URL'], commit_rel_url)
            tmp = {}
            tmp['title'] = c['title']
            tmp['created_at'] = c['created_at']  # There's also committed_at and authored_at, not sure which one to choose
            tmp['url'] = commit_abs_url
            latest_commits.append(tmp)
        return latest_commits

    def get_latest_tags(self):
        latest_tags = []
        project = self.repository_instance
        tags = project.tags.list()

        if len(tags) < self.settings['LATEST_TAGS_LIMIT']:
            limit = len(tags)
        else:
            limit = self.settings['LATEST_TAGS_LIMIT']

        for tag in tags[:limit]:
            t = tag.attributes
            tag_rel_url = self.settings['GITLAB_URL_TAG'].format(namespace=self.namespace,
                                                         name=t['name'])
            tag_abs_url = '{0}{1}'.format(self.settings['GITLAB_URL'], tag_rel_url)
            tmp = {}
            tmp['name'] = t['name']
            tmp['created_at'] = t['commit']['created_at']  # A tag is tied to a commit
            tmp['url'] = tag_abs_url
            latest_tags.append(tmp)
        return latest_tags

    def get_archive_url(self, extension='zip', ref='master'):
        path = self.settings['GITLAB_URL_ARCHIVE'].format(namespace=self.namespace,
                                                 extension=extension,
                                                 ref=ref)
        url = '{}{}'.format(self.settings['GITLAB_URL'], path)
        return url

    def get_commits_contributors(self):

        project = self.repository_instance
        contributors = project.repository_contributors()

        # Example response:
        # [{'name': 'Raphaël Voyazopoulos', 'email': "
        #  "'raphael.voyazopoulos@ircam.fr', 'commits': 2, 'additions': 0, 'deletions': "
        #  "0}, {'name': 'johndoe', 'email': 'johndoe@yopmail.com', 'commits': 1, "
        #  "'additions': 0, 'deletions': 0}]

        # NOTE: Contributors are *commits author*, not necessarily registered users on Forum or even Gitlab
        #       It's our job to map them to existing users if we need it.

        ret = []

        for contributor in contributors:
            tmp = {}
            tmp['display_name'] = contributor['name']
            tmp['email'] = contributor['email']
            tmp['extra_data'] = {
                'commits': contributor['commits'],
                'additions': contributor['additions'],
                'deletions': contributor['deletions'],
            }
            ret.append(tmp)

        return ret

    def get_issues_contributors(self):

        # NOTE: only counting issues authors
        # TODO: include issues participants

        project = self.repository_instance
        issues = project.issues.list()
        issues_authors = [issue.author for issue in issues]

        # Deduplicating
        contributors = []
        for c in issues_authors:
            if not dsh.collections.find(contributors, c):
                contributors.append(c)


        # Example response (only relevant part):
        # [{ ... 'author': {
        #    'id': 1,
        #    'name': 'Administrator',
        #    'username': 'root',
        #    'state': 'active',
        #    'avatar_url': 'http://www.gravatar.com/avatar/c128c3457d1d6a547627d9ddf3d2a6b7?s=80&d=identicon',
        #    'web_url': 'http://mills.ircam.fr:8099/root'
        # } ... }]

        ret = []

        for contributor in contributors:
            gitlab_user = self._get_user(username=contributor['username'])
            tmp = {}
            tmp['email'] = gitlab_user.email
            tmp['display_name'] = gitlab_user.name
            tmp['extra_data'] = {}
            ret.append(tmp)

        return ret

    def get_members(self):

        project = self.repository_instance
        contributors = project.members.list()

        # Example response (only relevant part):
        # [{'id': 41,
        #   'name': 'johndoe',
        #   'username': 'johndoe',
        #   'state': 'active',
        #   'avatar_url': 'http://www.gravatar.com/avatar/58aa4a5e3aad68d2d518857fee3ba691?s=80&d=identicon',
        #   'web_url': 'http://mills.ircam.fr:8099/johndoe',
        #   'access_level': 40,
        #   'expires_at': None}]

        ret = []

        for contributor in contributors:
            gitlab_user = self._get_user(username=contributor.username)
            tmp = {}
            tmp['email'] = gitlab_user.email
            tmp['display_name'] = gitlab_user.name
            tmp['extra_data'] = {
                "access_level": contributor.access_level
            }
            ret.append(tmp)

        return ret

    def get_languages(self):

        project = self.repository_instance
        ret = project.languages()

        return ret

    def get_edit_url(self, path):

        path = self.settings['GITLAB_URL_EDIT'].format(namespace=self.namespace,
                                                       branch="master",
                                                       path=path)

        return '{}{}'.format(self.host, path)