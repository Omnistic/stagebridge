import xml.etree.ElementTree as ET
import numpy as np
from .base import BaseHandler


class LeicaHandler(BaseHandler):
    def read(self, content: bytes, ext: str = "") -> np.ndarray:
        root = ET.fromstring(content)
        positions = []

        if ext == "maf":
            for mark in root.iter("XYZStagePointDefinition"):
                x = float(mark.attrib["StageXPos"])
                y = float(mark.attrib["StageYPos"])
                positions.append([x, y])
        elif ext == "nes":
            for shape_item in root.iter():
                type_el = shape_item.find("Type")
                if type_el is not None and type_el.text == "Point":
                    verticies = shape_item.find("Verticies/Items")
                    if verticies is not None:
                        for vertex in verticies:
                            x = float(vertex.find("X").text)
                            y = float(vertex.find("Y").text)
                            positions.append([x, y])
        else:
            raise ValueError(f"Unsupported Leica format: '{ext}'")

        if not positions:
            raise ValueError("No stage positions found in file")

        return np.array(positions) * 1e6

    def write(self, positions: np.ndarray, path: str):
        raise NotImplementedError(
            "Writing Leica files is not yet supported. "
            "Use ZeissHandler.write() to export positions for Zeiss."
        )