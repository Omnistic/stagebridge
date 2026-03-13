import xml.etree.ElementTree as ET
import numpy as np
from .base import BaseHandler

class ZeissHandler(BaseHandler):
    def read(self, content: bytes) -> np.ndarray:
        root = ET.fromstring(content)
        positions = [
            [float(mark.attrib["X"]), float(mark.attrib["Y"])]
            for mark in root.findall("StageMark")
        ]
        return np.array(positions)
    
    def write(self, positions: np.ndarray, path: str, z_safe: float = 0.0):
        root = ET.Element("StageMarks")
        for i, pos in enumerate(positions):
            ET.SubElement(root, "StageMark",
                ItemIndex=str(i + 1),
                X=str(round(pos[0], 1)),
                Y=str(round(pos[1], 1)),
                Z=str(z_safe)
            )
        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(path, xml_declaration=True, encoding="utf-8")