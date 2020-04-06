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

        html_content = ''
        raw_content = ''
        content_type = None
        path = None

        for file, file_type in readme_tests:
            try:
                raw_content = vendor_method(file)
                path = file
            except Exception:
                file = None
            else:
                content_type = file_type

        if content_type == 'md':
            if 'md_parser' in kwargs and callable(kwargs['md_parser']):
                html_content = kwargs['md_parser'](raw_content)
            else:
                html_content = markdown.markdown(raw_content)
        elif content_type == 'rst':
            if 'rst_parser' in kwargs and callable(kwargs['rst_parser']):
                html_content = kwargs['rst_parser'](raw_content)
            else:
                html_content = publish_parts(raw_content, writer_name='html')
                html_content = html_content['body']
        elif content_type == 'raw':
            if 'raw_parser' in kwargs and callable(kwargs['raw_parser']):
                html_content = kwargs['raw_parser'](raw_content)
            else:
                html_content = '<br>'.join(raw_content.split('\n'))  # \n to <br>

        return (path, html_content)
