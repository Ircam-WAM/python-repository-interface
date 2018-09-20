from .utils import VendorInterface
from github import Github
import markdown
from urllib.parse import urlparse, urljoin
import pydash as dsh


class GithubRepository(VendorInterface):

    url = None
    host = None
    namespace = None
    instance = None
    settings = None

    def __init__(self, url, settings={}, **kwargs):

        self.url = url
        self.settings = settings
        debug_mode = kwargs['debug'] if 'debug' in kwargs else False
        parsed_url = urlparse(self.url)

        # Testing HTTPS
        # TODO: handle SSH as well (with public key kwarg?)
        if not debug_mode:
            if parsed_url.scheme != 'https':
                raise Exception("Repository must use HTTPS")

        self.host = parsed_url.scheme + '://' + parsed_url.netloc
        self.namespace = parsed_url.path[1:]  # Stripping the first slash

        self.instance = Github(self.settings['API_TOKEN'])

    def _get_user(self, username=None):
        return self.instance.get_user(username)

    def _get_user_name(self, username=None):
        u = self.instance.get_user(username)
        display_name = u.name if u.name != '' else u.login
        return display_name

    def get_instance(self):
        return self.instance

    def get_readme(self):

        repository = self.instance.get_repo(self.namespace)
        f = repository.get_file_contents('README.md', ref='master')
        f = f.content
        # TODO: scan for READMEs (md, rst, txt)
        # IDEA: let user choose file and branch in the project settings
        # IDEA: checkout the defined main branch of the repo instead of master

        import base64
        f = base64.standard_b64decode(f)
        markdown_content = f.decode('utf-8')
        html_content = markdown.markdown(markdown_content)

        return html_content

    def get_summary(self):

        summary = {
            'latest_commits': self.get_latest_commits(),
            'latest_tags': self.get_latest_tags()
        }

        return summary

    def get_latest_commits(self):

        latest_commits = []
        repository = self.instance.get_repo(self.namespace)
        commits = repository.get_commits()

        if commits.totalCount < self.settings['LATEST_COMMITS_LIMIT']:
            limit = commits.totalCount
        else:
            limit = self.settings['LATEST_COMMITS_LIMIT']

        # TODO: add a limit!
        for commit in commits[:limit]:
            c = commit.commit
            tmp = {}
            tmp['title'] = c.message
            tmp['created_at'] = c.author.date
            tmp['url'] = c.html_url
            latest_commits.append(tmp)
        return latest_commits

    def get_latest_tags(self):

        latest_tags = []
        repository = self.instance.get_repo(self.namespace)
        tags = repository.get_tags()

        if tags.totalCount < self.settings['LATEST_TAGS_LIMIT']:
            limit = tags.totalCount
        else:
            limit = self.settings['LATEST_TAGS_LIMIT']

        for tag in tags[:limit]:
            tmp = {}
            tmp['name'] = tag.name
            tmp['created_at'] = tag.commit.author.date
            tmp['url'] = tag.commit.html_url
            latest_tags.append(tmp)
        return latest_tags

    def get_archive_url(self, extension='zip', ref='master'):
        path = self.settings['GITHUB_URL_ARCHIVE'].format(namespace=self.namespace,
                                                 extension=extension,
                                                 ref=ref)
        url = '{}{}'.format(self.settings['GITHUB_URL'], path)
        return url

    def get_commits_contributors(self):

        repo = self.instance.get_repo(self.namespace)
        contributors = repo.get_stats_contributors()

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
            tmp['display_name'] = self._get_user_name(username=contributor.author.login)

            # Email is not directly disclosed, have to get it by another API call
            tmp['email'] = self._get_user(username=contributor.author.login).email

            tmp['extra_data'] = {
                'commits': contributor.total,
            }
            ret.append(tmp)

        return ret

    def get_issues_contributors(self):

        # NOTE: only counting issues authors
        # TODO: include issues participants

        repo = self.instance.get_repo(self.namespace)
        issues = repo.get_issues()
        issues_authors = [issue.user for issue in issues]

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
            github_user = self._get_user(username=contributor.login)
            tmp = {}
            tmp['email'] = github_user.email
            tmp['display_name'] = self._get_user_name(username=github_user.login)
            tmp['extra_data'] = {}
            ret.append(tmp)

        return ret

    def get_members(self):
        # Push permission is needed to view a Github repo's members (aka collaborators)
        # Before we allow users to specify a personal token, returning an empty array
        # repo.get_collaborators()
        return []
