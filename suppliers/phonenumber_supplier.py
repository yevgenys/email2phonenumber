import os
import re
from copy import copy

from suppliers import Supplier, USPhoneNumberSupplier


def dump_supplied_phones(output_file, possible_phone_numbers, colors):
    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(possible_phone_numbers))
        print(colors.GREEN + "Dictionary created successfully at " + os.path.realpath(f.name) + colors.ENDC)
    else:
        print(colors.GREEN + "There are " + str( len(possible_phone_numbers)) + " possible numbers" + colors.ENDC)
        print(colors.GREEN + str(possible_phone_numbers) + colors.ENDC)


class PhonenumberSupplier(Supplier):
    def __init__(self, settings, user_agent_instance, proxy_instance, colors, mask):
        self.region = settings.region
        self.mask = mask
        self.colors = colors
        self.cache = {}
        self.map_region = {
            "US": USPhoneNumberSupplier(self.cache, user_agent_instance, proxy_instance, copy(self.mask))
        }

    def supply(self):
        if not re.match("^[0-9X]{10}", self.mask):
            exit(self.colors.RED + "You need to pass a US phone number masked as in: 555XXX1234" + self.colors.ENDC)

        return self.map_region[self.region].supply()
