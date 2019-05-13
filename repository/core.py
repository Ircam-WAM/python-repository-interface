import os, re
from repository.api import IRepository
from repository.component import implementations, Component, MetaComponent, abstract, implements


_repositories = {}


class MetaRepository(MetaComponent):
    """Metaclass of the Repository class, used mainly for ensuring
    that repository id's are wellformed and unique"""

    valid_id = re.compile("^[a-z][_a-z0-9]*$")

    def __new__(cls, name, bases, d):
        new_class = super(MetaRepository, cls).__new__(cls, name, bases, d)
        if new_class in implementations(IRepository):
            id = str(new_class.id())
            if id in _repositories:
                # Doctest test can duplicate a processor
                # This can be identify by the conditon "module == '__main__'"
                new_path = os.path.realpath(inspect.getfile(new_class))
                id_path = os.path.realpath(inspect.getfile(_repositories[id]))
                if new_class.__module__ == '__main__':
                    new_class = _repositories[id]
                elif _repositories[id].__module__ == '__main__':
                    pass
                elif new_path == id_path:
                    new_class = _repositories[id]
                else:
                    raise ApiError("%s and %s have the same id: '%s'"
                                   % (new_class.__name__,
                                      _repositories[id].__name__, id))
            if not MetaRepository.valid_id.match(id):
                raise ApiError("%s has a malformed id: '%s'"
                               % (new_class.__name__, id))

            _repositories[id] = new_class

        return new_class


class Repository(Component, metaclass=MetaRepository):

    url = None
    vendor = None
    vendor_client = None
    vendor_instance = None
    debug = False

    abstract()
    implements(IRepository)


def repositories(interface=IRepository, recurse=True):
    """Returns the objects implementing a given interface and, if recurse,
    any of the descendants of this interface."""
    return implementations(interface, recurse)


def list_repositories(interface=IRepository, prefix=""):
    print(prefix + interface.__name__)
    if len(prefix):
        underline_char = '-'
    else:
        underline_char = '='
    print(prefix + underline_char * len(interface.__name__))
    subinterfaces = interface.__subclasses__()
    procs = repositories(interface, False)
    for p in procs:
        print(prefix + "  * %s :" % p.id())
        print(prefix + "    \t\t%s" % p.name())

