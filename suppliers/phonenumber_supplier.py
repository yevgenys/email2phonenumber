import os

from suppliers.us_phonenumber_supplier import USPhoneNumberSupplier


class PhonenumberSupplier:
    def __init__(self, settings, user_agent_instance, proxy_instance, colors, mask):
        self.region = settings.region
        self.colors = colors
        self.map_region = {
            "US": USPhoneNumberSupplier({}, user_agent_instance, proxy_instance, colors, mask)
        }

    def get(self):
        if self.region not in self.map_region:
            exit(f"{self.region} is not supported yet. ")

        return self.map_region[self.region].supply()

    def get_from_dump(self, input_file):
        if input_file:
            with open(input_file, "r") as f:
                return filter(None, f.readlines())  # Remove last \n if needed
        exit("File path not provided")

    def dump_supplied_phones(self, output_file, possible_phone_numbers):
        if output_file:
            with open(output_file, 'w') as f:
                f.write('\n'.join(possible_phone_numbers))
            print(self.colors.GREEN + "Dictionary created successfully at " + os.path.realpath(f.name) + self.colors.ENDC)
        else:
            print(self.colors.GREEN + "There are " + str(len(possible_phone_numbers)) + " possible numbers" + self.colors.ENDC)
            print(self.colors.GREEN + str(possible_phone_numbers) + self.colors.ENDC)
