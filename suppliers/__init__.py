import abc

from suppliers.us_phonenumber_supplier import USPhoneNumberSupplier


class Supplier(object):
    @abc.abstractmethod
    def supply(self):
        pass
