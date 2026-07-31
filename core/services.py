"""
Atlas V3 Base Service
"""

from abc import ABC, abstractmethod


class Service(ABC):

    @abstractmethod
    def start(self):
        """Start the service."""
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        """Stop the service."""
        raise NotImplementedError