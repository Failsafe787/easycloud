"""
EasyCloud ActionBinder component for handling the
association of actions and methods of each platform
"""

import collections

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"

_manager_actions = collections.defaultdict(dict)


def bind_action(_manager, _name):
    """
    Decorator for registering an action for a platform

    Args:
        _manager (str): the platform class name
        _name (str): the action name

    Returns:
        func: the decorator function
    """
    def _bind(_func):
        _m_name = _func.__name__
        _manager_actions[_manager][_name] = _m_name
        return _func
    return _bind


def get_actions(_manager):
    """
    Returns all the registered actions for a specific platform

    Args:
        _manager (str): the platform class name

    Returns:
        dict: a structure containing all the actions for a platform
    """
    return _manager_actions[_manager]
