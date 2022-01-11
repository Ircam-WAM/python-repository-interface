from abc import ABC, abstractmethod
import markdown
import re
import os
import bleach
from docutils.core import publish_parts
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class VendorInterface(ABC):

    @abstractmethod
    def get_readme(self):
        pass

    @abstractmethod
    def get_summary(self):
        pass


def is_relative_url(url):
    parsed = urlparse(url)
    # only filtering basic anchors,
    # stuff like "./#foobar" would pass anyway...
    is_anchor = url[0] == "#"
    has_netloc = bool(parsed.netloc)
    return not has_netloc and not is_anchor


class VendorMixin:

    default_markdown_extensions = [
        # pymdownx uses pygments for syntax highlighting
        # NB: code block language is not auto-detected
        # https://facelessuser.github.io/pymdown-extensions/extensions/superfences/#code-highlighting
        'pymdownx.extra',
        'pymdownx.magiclink',
        'pymdownx.tasklist',
        'mdx_truly_sane_lists',
    ]
    default_markdown_extension_configs = {}

    def _rel_to_abs_links(self, html, default_branch="master"):
        """ Rewrite relative links to absolute links in a HTML string """

        link_pattern = r"<a[^>]*href=[\"']([^\"']*)[\"'][^>]*>.*<\/a>"
        unique_rel_links = [link for link in re.findall(link_pattern, html) if is_relative_url(link)]
        # gives us a deduplicated list of relative links across the HTML
        unique_rel_links = list(set(unique_rel_links))

        for rel_link in unique_rel_links:
            # ./README.md == doc/../README.md == README.md
            normalized_path = os.path.normpath(rel_link)
            if normalized_path[:3] == '../':
                # As READMEs are always at the root
                # (and until we use this function for something else than READMEs),
                # if the normalized relative link begins with ../
                # we just ignore it as it would create a broken absolute link.
                continue
            # absolute URL is the same for github and gitlab
            abs_link = f"{self.host}/{self.namespace}/blob/{default_branch}/{normalized_path}"

            # Using re.sub because we want to replace whole hrefs
            # which might be with single or double quotes.
            # NOTE: we use the captured path and not the normalized one!
            html = re.sub(r"href=[\"']{}[\"']".format(rel_link),
                          'href="{}"'.format(abs_link),
                          html)

        return html

    def _rel_to_abs_img(self, html, default_branch="master"):
        soup = BeautifulSoup(html, features="html.parser")
        for img in soup.findAll('img'):
            url = img['src']
            if not is_relative_url(url):
                continue
            normalized_path = os.path.normpath(url)
            if normalized_path[:3] == '../':
                continue
            img['src'] = f"{self.host}/{self.namespace}/raw/{default_branch}/{normalized_path}"
        return str(soup)

    def _find_readme(self, vendor_method, readme_tests=[], **kwargs):
        # vendor_method must return the raw document string (utf-8)
        # or raise an exception, and takes a sole argument that i the file path to check

        html_content = None
        raw_content = None
        readme_path = None
        readme_format = None

        # Default parsers if the method is called without a custom parser
        default_parsers = {
            'md': lambda raw: markdown.markdown(
                raw,
                extensions=self.default_markdown_extensions,
                extension_configs=self.default_markdown_extension_configs
            ),
            'rst': lambda raw: publish_parts(raw, writer_name='html')['body'],
            'raw': lambda raw: '<br>'.join(raw.split('\n')),  # \n to <br>
        }

        for test_path, test_format in readme_tests:
            try:
                raw_content = vendor_method(test_path)
                readme_path = test_path
                readme_format = test_format
            except Exception:
                pass
            else:
                break

        # If a README file wasn't found, return an empty string as HTML content
        if raw_content is None or readme_path is None or readme_format is None:
            html_content = ''

        # Else, parse it given its format and return the result
        else:
            custom_parser = '{}_parser'.format(readme_format)
            try:
                if custom_parser in kwargs and callable(kwargs[custom_parser]):
                    html_content = kwargs[custom_parser](raw_content)
                else:
                    raise Exception()
            except Exception:
                # Executed wether the custom parser fails or there isn't one
                html_content = default_parsers[readme_format](raw_content)

            # Clean user input with an allowlist of html tags and attributes
            html_content = bleach.clean(
                html_content,
                tags=[
                    # Tags generated by markdown
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'b', 'i', 'strong', 'em', 'tt',
                    'p', 'br',
                    'span', 'div', 'blockquote', 'code', 'pre', 'hr',
                    'ul', 'ol', 'li', 'dd', 'dt',
                    'img',
                    'a',
                    'sub', 'sup',

                    # Extra tags allowed by user-defined HTML
                    'audio',
                    'source'
                ],
                attributes={
                    # id is mandatory for link anchors
                    # class is mandatory for syntax highlighting
                    '*': ['id', 'class'],
                    'img': ['src', 'alt', 'title'],
                    'a': ['href', 'alt', 'title'],

                    'audio': ['src', 'controls'],
                    'source': ['src', 'type']
                })

        return (readme_path, html_content)
