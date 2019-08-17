import abc

class Supplier(object):
    @abc.abstractmethod
    def supply(self):
        pass
