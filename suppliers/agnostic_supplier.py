from constants import PHONE_NUMBER
from suppliers.phonenumber_supplier import PhonenumberSupplier


class AgnosticSupplier:
    supplier_map = {
        PHONE_NUMBER: PhonenumberSupplier
    }

    @staticmethod
    def get_supplier(supplier_type):
        if supplier_type not in AgnosticSupplier.supplier_map:
            raise Exception(f"{supplier_type} is unknown.")

        return AgnosticSupplier.supplier_map[supplier_type]
