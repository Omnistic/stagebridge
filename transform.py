import numpy as np
import json, os

def calculate_transform(positions_a, positions_b):
    if len(positions_a) != len(positions_b):
        raise ValueError("The same number of positions must be provided for Microscope A and B")

    positions_a = np.array(positions_a)
    positions_b = np.array(positions_b)

    centroid_a = positions_a.mean(axis=0)
    centroid_b = positions_b.mean(axis=0)

    centered_a = positions_a - centroid_a
    centered_b = positions_b - centroid_b

    scaling = np.sqrt(np.sum(centered_b**2) / np.sum(centered_a**2))

    scaled_a = centered_a * scaling

    H = centered_b.T @ scaled_a
    U, _, Vt = np.linalg.svd(H)
    rotation = U @ Vt
    if np.linalg.det(rotation) < 0:
        U[:, -1] *= -1
        rotation = U @ Vt

    return centroid_a, centroid_b, scaling, rotation

def apply_transform(positions, centroid_a, centroid_b, scaling, rotation):
    return (positions - centroid_a) * scaling @ rotation.T + centroid_b

def write_transform(transform, filename):
    os.makedirs("available_transforms", exist_ok=True)
    with open(f"available_transforms/{filename}.json", "w") as f:
        json.dump(transform, f, indent=2)

def read_transform(filename):
    with open(f"available_transforms/{filename}.json") as f:
        return json.load(f)