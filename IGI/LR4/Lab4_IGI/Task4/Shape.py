from abc import ABC, abstractmethod

class Shape(ABC):
    """Abstract base class for shapes"""

    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def draw(self):
        pass