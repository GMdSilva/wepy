import sys

import numpy as np

from wepy.walker import Walker

class BoundaryConditions(object):
    def __init__(self, **kwargs):
        raise NotImplementedError

    def check_boundaries(self, walker):
        """ Checks if a walker is in a boundary and returns which boundary it is in"""
        raise NotImplementedError

    def warp_walkers(self, walkers):
        """Checks walkers for membership in boundaries and processes them
        according to the rules of the boundary."""
        raise NotImplementedError


class NoBC(BoundaryConditions):

    def check_boundaries(self, walker):
        return False

    def warped_walkers(self, walkers):
        return walkers, []
