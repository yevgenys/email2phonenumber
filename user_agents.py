import itertools


class UserAgentsCycle(object):
    def __init__(self):
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
        try:
            with open('./user_agents.ini', 'r') as f:
                return filter(None, f.readlines())  # filter new line in the end, if present
        except Exception as e:
            print("Error: {}".format(str(e)))
            exit("Not able to read user agents, check that file ./email2phonenumber/scrapers/user_agents.ini is present and contains data")
