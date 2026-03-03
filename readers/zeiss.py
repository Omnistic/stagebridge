import xml.etree.ElementTree as ET
import numpy as np
from .base import BaseReader

class ZeissReder(BaseReader):
    def read(self, content: bytes):
        root = ET.fromstring(content)
        positions = [
            [float(mark.attrib["X"]), float(mark.attrib["Y"])]
            for mark in root.findall("StageMark")
        ]
        return np.array(positions)