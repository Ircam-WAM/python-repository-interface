from abc import ABC, abstractmethod

class VendorInterface(ABC):

  @abstractmethod
  def get_readme(self):
    pass

  @abstractmethod
  def get_summary(self):
    pass