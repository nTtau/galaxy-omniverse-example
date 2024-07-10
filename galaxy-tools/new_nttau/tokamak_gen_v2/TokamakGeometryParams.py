import json
from dataclasses import dataclass, asdict


@dataclass
class TokamakGeometryParams:
    aspect_ratio: float  # Aspect ratio of the tokamak.
    radial_build: list[float]  # List of radii for the tokamak components.
    component_names: list[str]  # List of names for the tokamak components.
    tf_radius: float  # Radius of the toroidal field coils.
    tf_dz: float  # Vertical distance between the toroidal field coils.
    tf_dr: float  # Radial distance between the toroidal field coils.
    # List of coil specifications for the poloidal field (PF) coils
    #  of Menard coil params [r(m), z(m), dr(m), dz(m)]
    coils: list[float]


def load_params_json(input_file: str) -> TokamakGeometryParams:
    with open(input_file, 'r') as f:
        data = json.load(f)
        assert len(data['radial_build']) == len(data['component_names'])
        return TokamakGeometryParams(**data)


def save_params_json(params: TokamakGeometryParams, file_path: str):
    data = asdict(params)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
