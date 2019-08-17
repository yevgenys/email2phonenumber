from suppliers.phonenumber_supplier import PhonenumberSupplier

class AgnosticSupplier(object):
    supplier_map = {
        "phone_number": PhonenumberSupplier
    }


    @staticmethod
    def get_supplier(supplier_type):
        if supplier_type not in AgnosticSupplier.supplier_map:
            raise Exception(f"{supplier_type} is unknown.")
        
        return AgnosticSupplier.supplier_map[supplier_type]