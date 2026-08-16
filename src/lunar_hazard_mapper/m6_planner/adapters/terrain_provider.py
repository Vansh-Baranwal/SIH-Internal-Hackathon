from abc import ABC, abstractmethod

class TerrainProvider(ABC):
    """
    Interface for providing lunar terrain elevation data.
    """
    @abstractmethod
    def get_height(self, x: float, y: float) -> float:
        """
        Returns the terrain elevation (Z coordinate) at the given (X, Y) location.
        """
        pass

class MockTerrainProvider(TerrainProvider):
    """
    Mock implementation of TerrainProvider for independent M6 development.
    Can be configured to return a flat terrain or a simple analytical surface.
    """
    def __init__(self, base_height: float = 0.0):
        self.base_height = base_height
        
    def get_height(self, x: float, y: float) -> float:
        """
        Currently returns a flat terrain at base_height.
        Future extensions can add craters/slopes using math functions.
        """
        return self.base_height
