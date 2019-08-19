import itertools
import os


class UserAgentsCycle:
    """
    the idea is to get always next/new, instead of random - to not use same agent twice
    """
    def __init__(self, settings):
        self._settings = settings
        self._user_agents = itertools.cycle(self._read())

    def next(self):
        return next(self._user_agents)

    def _read(self):
        """
        format of user_agents.ini file - each agent should be in the new line, the file will be consumed line by line.
        ex.:
        Agent 1\n
        Agent 2\n
        Agent 3\n
        """
        file_path = os.path.join(self._settings.root_dir, 'core', 'user_agents.ini')
        try:
            with open(file_path, 'r') as f:
                # made read and split, instead of readlines, to remove '\n' character
                return filter(None, f.read().split('\n'))  # filter new line in the end, if present
        except Exception as e:
            print("Error: {}".format(str(e)))
            exit("Not able to read user agents, check that file {} is present and contains data".format(file_path))
