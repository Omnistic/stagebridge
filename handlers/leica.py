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
        elif ext in ("nes", "rgn"):
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

    def write(self, positions: np.ndarray, path: str, z_safe: float = 0.0):
        root = ET.Element("StageOverviewRegions")
        items = ET.SubElement(
            ET.SubElement(ET.SubElement(root, "Regions"), "ShapeList"), "Items"
        )
        for i, pos in enumerate(positions):
            item = ET.SubElement(items, f"Item{i}")
            ET.SubElement(item, "Name").text = f"Region{i + 1}"
            ET.SubElement(item, "Type").text = "Point"
            ET.SubElement(item, "Visible").text = "true"
            vertex = ET.SubElement(
                ET.SubElement(ET.SubElement(item, "Verticies"), "Items"), "Item0"
            )
            # Leica stores positions in meters, we work in micrometers
            ET.SubElement(vertex, "X").text = f"{pos[0] / 1e6:.10f}"
            ET.SubElement(vertex, "Y").text = f"{pos[1] / 1e6:.10f}"
            ET.SubElement(vertex, "Z").text = f"{z_safe / 1e6:.10g}"
            ET.SubElement(vertex, "T").text = "0"
        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(path, encoding="utf-8")