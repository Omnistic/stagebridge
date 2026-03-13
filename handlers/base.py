from abc import ABC, abstractmethod
import numpy as np

class BaseHandler(ABC):
    @abstractmethod
    def read(self, content: bytes) -> np.ndarray:
        pass

    @abstractmethod
    def write(self, positions: np.ndarray, path: str):
        pass