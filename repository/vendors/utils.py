from abc import ABC, abstractmethod
import markdown
import re
import os
from docutils.core import publish_parts
from urllib.parse import urlparse


class VendorInterface(ABC):

    @abstractmethod
    def get_readme(self):
        pass

    @abstractmethod
    def get_summary(self):
        pass


class VendorMixin:

    default_markdown_extensions = ['pymdownx.extra', 'pymdownx.magiclink', 'pymdownx.tasklist', 'mdx_truly_sane_lists']
    default_markdown_extension_configs = {}

    def _rel_to_abs_links(self, html, template=None):
        """ Rewrite relative links to absolute links in a HTML string """

        def is_relative_url(url):
            parsed = urlparse(url)
            is_anchor = url[0] == "#"  # Only filtering basic anchors, stuff like "./#foobar" would pass anyway...
            has_netloc = bool(parsed.netloc)
            return not has_netloc and not is_anchor

        link_pattern = r"<a[^>]*href=[\"']([^\"']*)[\"'][^>]*>.*<\/a>"
        unique_rel_links = [link for link in re.findall(link_pattern, html) if is_relative_url(link)]
        unique_rel_links = list(set(unique_rel_links))
        # ^ gives us a deduplicated list of relative links across the HTML ^

        for rel_link in unique_rel_links:
            normalized_path = os.path.normpath(rel_link)  # ./README.md == doc/../README.md == README.md
            if normalized_path[:3] == '../':
                # As READMEs are always at the root (and until we use this function for something else than READMEs),
                # if the normalized relative link begins with ../ we just ignore it as it would create a broken absolute link.
                continue
            abs_link = template.format(host=self.host, namespace=self.namespace, rel_path=normalized_path)

            # Using re.sub because we want to replace whole hrefs
            # which might be with single or double quotes.
            html = re.sub(r"href=[\"']{}[\"']".format(rel_link),  # NOTE: we use the captured path and not the normalized one!
                          'href="{}"'.format(abs_link),
                          html)

        return html

    def _find_readme(self, vendor_method, readme_tests=[], **kwargs):

        # vendor_method must return the raw document string (utf-8)
        # or raise an exception, and takes a sole argument that is
        # the file path to check

        html_content = None
        raw_content = None
        readme_path = None
        readme_format = None

        # Default parsers if the method is called without a custom parser
        default_parsers = {
            'md': lambda raw: markdown.markdown(raw,
                                                extensions=self.default_markdown_extensions,
                                                extension_configs=self.default_markdown_extension_configs),
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

        return (readme_path, html_content)
