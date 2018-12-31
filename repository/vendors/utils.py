from abc import ABC, abstractmethod
import markdown
from docutils.core import publish_parts

class VendorInterface(ABC):

  @abstractmethod
  def get_readme(self):
    pass

  @abstractmethod
  def get_summary(self):
    pass


class VendorMixin:

    def _find_readme(self, vendor_method, readme_tests=[]):

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
            html_content = markdown.markdown(raw_content)
        elif content_type == 'rst':
            html_content = publish_parts(raw_content, writer_name='html')
            html_content = html_content['body']
        elif content_type == 'raw':
            html_content = '<br>'.join(raw_content.split('\n'))  # \n to <br>

        return (path, html_content)
