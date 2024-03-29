from .utils import VendorInterface, VendorMixin
from github import Github
from urllib.parse import urlparse, urljoin
import pydash as dsh
import base64


class GithubRepository(VendorInterface, VendorMixin):

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
        # TODO: handle SSH as well (with public key kwarg?)
        if not debug_mode:
            if parsed_url.scheme != 'https':
                raise Exception("Repository must use HTTPS")

        self.host = parsed_url.scheme + '://' + parsed_url.netloc
        self.namespace = parsed_url.path[1:]  # Stripping the first slash

        self.host_instance = Github(self.settings['API_TOKEN'])
        self.repository_instance = self.host_instance.get_repo(self.namespace)

    def _get_user(self, username=None):
        return self.host_instance.get_user(username)

    def _get_user_name(self, username=None):
        u = self.host_instance.get_user(username)
        display_name = u.name if u.name != '' else u.login
        return display_name

    def get_host_instance(self):
        return self.host_instance

    def get_repository_instance(self):
        return self.repository_instance

    def get_readme(self):
        repository = self.repository_instance

        def find_func(path):
            f = repository.get_contents(path, ref=repository.default_branch)
            f = f.content
            f = base64.standard_b64decode(f)
            return f.decode('utf-8')

        # Finds readme and returns HTML
        path, html_content = super()._find_readme(
                find_func,
                readme_tests=self.settings['README_TESTS']
        )

        # Replace relative links by absolute links in HTML
        html_content = self._rel_to_abs_links(
            html_content,
            default_branch=repository.default_branch
        )

        html_content = self._process_img(
            html_content,
            default_branch=repository.default_branch
        )

        return (path, html_content)

    def get_summary(self):

        summary = {
            'latest_commits': self.get_latest_commits() if not self.private else None,
            'latest_tags': self.get_latest_tags()
        }

        return summary

    def get_latest_commits(self):

        latest_commits = []
        repository = self.repository_instance
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
        repository = self.repository_instance
        tags = repository.get_tags()

        if tags.totalCount < self.settings['LATEST_TAGS_LIMIT']:
            limit = tags.totalCount
        else:
            limit = self.settings['LATEST_TAGS_LIMIT']

        for tag in tags[:limit]:
            tag_rel_url = self.settings['GITHUB_URL_TAG'].format(namespace=self.namespace,
                                                                 name=tag.name)
            tag_abs_url = '{0}{1}'.format(self.settings['GITHUB_URL'], tag_rel_url)
            tmp = {}
            tmp['name'] = tag.name
            tmp['created_at'] = tag.commit.commit.author.date  # Because tag.commit.author returns a NamedUser
                                                               # whereas tag.commit.commit.author returns a GitAuthor
            tmp['url'] = tag_abs_url if not self.private else None
            latest_tags.append(tmp)
        return latest_tags

    def get_archive_url(self, extension='zip', ref=None):
        if ref is None:
            ref = self.repository_instance.default_branch
        path = self.settings['GITHUB_URL_ARCHIVE'].format(namespace=self.namespace,
                                                 extension=extension,
                                                 ref=ref)
        url = '{}{}'.format(self.settings['GITHUB_URL'], path)
        return url

    def get_commits_contributors(self):

        repo = self.host_instance.get_repo(self.namespace)
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

        repo = self.repository_instance
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

    def get_languages(self):

        repo = self.repository_instance
        languages = repo.get_languages()  # Returns {lang: bytes}
                                          # and not {lang: %} like GitLab

        # Returning % instead of bytes for each languages
        total = dsh.collections.reduce_(languages, lambda m, v, k: v + m, 0)
        ret = dsh.objects.map_values(languages, lambda v: round(v * 100 / total))

        return ret

    def get_edit_url(self, path):

        branch = self.repository_instance.default_branch
        path = self.settings['GITHUB_URL_EDIT'].format(namespace=self.namespace,
                                                       branch=branch,
                                                       path=path)

        return '{}{}'.format(self.host, path)

    @property
    def private(self):
        return self.repository_instance.private

    # Untested yet
    # def delete(self):
    #     self.repository_instance.delete()
