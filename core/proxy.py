import random

from constants import RED, ENDC


class Proxy(object):
    def __init__(self, settings):
        self._file_path = settings.path_to_proxy_file
        self._parsed_proxies = []
        self._parsed = False
        self._verify_proxy = settings.verify_proxy

    @property
    def verify_proxy(self):
        return self._verify_proxy

    def get_random_proxy(self):
        if not self._parsed:
            self._read_and_parse_proxy_list()

        return random.choice(self._parsed_proxies) if self._parsed_proxies else None

    def _read_and_parse_proxy_list(self):
        """
        TODO: describe file proxy format(s)
        """
        try:
            if self._file_path:
                with open(self._file_path, "r") as f:
                    file_content = f.read()
                    file_content = filter(None, file_content)  # Remove last \n if needed
                    proxy_list_unformatted = file_content.split("\n")
                    for proxy_unformatted in proxy_list_unformatted:
                        separator_position = proxy_unformatted.find("://")
                        self._parsed_proxies.append(
                            {proxy_unformatted[:separator_position]: proxy_unformatted[separator_position + 3:]})

            self._parsed = True
        except Exception as e:
            exit(RED + "{}Could not read file {};\nException: {}{}".format(RED, self._file_path, str(e), ENDC))
