# pylint: disable=import-error
"""
This module contains the Torus class which is used to generate a 3D model of a torus-shaped tokamak.

The Torus class extends the Workplane class from the CadQuery library.
It uses various geometric parameters to define the
shape of the torus and can generate
either a solid model or a wireframe based on these parameters.

This module also includes the tf_step function from the tf_step_v3 module,
which is used to create a toroidal field coil assembly.

The module uses constants to represent full and half revolve for better code readability.

Dependencies:
- csv: for reading data from CSV files
- os: for handling file and directory paths
- itertools: for advanced iteration tools like accumulate
- typing: for type hints
- cadquery: for 3D modeling
- numpy: for numerical operations
- paramak: for parametric 3D modeling in nuclear fusion research
- pylab: for scientific and technical computing
- tf_step_V3: for creating a toroidal field coil assembly
"""
import csv
import os
from itertools import accumulate
from typing import Tuple

import cadquery as cq
import numpy as np
import paramak
from TokamakGeometryParams import TokamakGeometryParams

# Defining constants for magic numbers
FULL_REVOLVE = 360
HALF_REVOLVE = 180


class Torus(cq.Workplane):
    """
    Class for creating a torus using CadQuery.

    Parameters:
        r_0 : float : Major radius ∏of the torus. Default is 2.2.
        aspect_ratio : float : Aspect Ratio. Default is 1.7.
        a : float : Minor radius of the torus.
        delta, si, sj, kappa, po : Various geometric parameters.
        degrees : int : Degrees to revolve. Default is 180.
        wire : bool : Whether to create a wireframe. Default is False.
        revolve_num : int : Number of revolves. Default is 1.
    """

    def __init__(
        self,
        r_0: float = 2.2,
        aspect_ratio: float = 2,
        a: float = None,
        delta: float = 0.5,
        si: float = 0.0,
        sj: float = 0.0,
        kappa: float = 2.36,
        po: int = 54,
        degrees: int = 180,
        wire: bool = False,
        revolve_num: int = 1,
    ):
        self.r_0 = r_0 if r_0 is not None else aspect_ratio * a
        self.aspect_ratio = aspect_ratio
        self.a = a if a is not None else r_0 / aspect_ratio
        self.delta = delta
        self.si = si
        self.sj = sj
        self.kappa = kappa
        self.po = po
        self.degrees = degrees
        self.wire = wire
        self.revolve_num = revolve_num
        self.construct_torus()

    def calculate_r(self, i: int) -> float:
        """
        Calculate the R-coordinate for a given index i.

        Parameters:
            i : int : Index in the loop to generate R and Z points.
        Returns:
            float : Calculated R value.
        """

        return self.r_0 + self.a * np.cos(
            np.pi
            + (i * np.pi / self.po)
            + (self.a * np.sin(self.delta)) *
            np.sin(np.pi + (i * np.pi / self.po))
        )

    def calculate_z(self, i: int, squaredness: float) -> float:
        """
        Calculate the Z-coordinate for a given index i.

        Parameters:
            i : int : Index in the loop to generate R and Z points.
            squaredness : float : Parameter to adjust the "squareness" of the torus.
        Returns:
            float : Calculated Z value.
        """

        return (
            self.a
            * self.kappa
            * np.sin(
                np.pi
                + (i * np.pi / self.po)
                + squaredness * np.sin(np.pi + (2 * i * np.pi / self.po))
            )
        )

    def get_r_and_z_points(self) -> Tuple[list, list]:
        """
        Generate the R and Z points to construct the torus.

        Returns:
            Tuple[list, list] : Lists of R and Z points.
        """

        r_points = []
        z_points = []

        for i in range(1, (2 * self.po)):
            r_val = self.calculate_r(i)
            z_val = self.calculate_z(i, self.si if i <= self.po else self.sj)

            r_points.append(np.round(r_val, 5))
            z_points.append(np.round(z_val, 5))

        return r_points, z_points

    def construct_torus(self):
        """
        Construct the torus using CadQuery. The constructed torus is stored in self.torus.
        """

        r_points, z_points = self.get_r_and_z_points()
        points = [[r, z] for r, z in zip(r_points, z_points)]

        radial_build_wire = cq.Workplane("XY").polyline(points).close()

        if not self.wire:
            self.torus = radial_build_wire.revolve(
                self.degrees, (0, -10, 0), (0, 10, 0)
            )
        else:
            self.torus = radial_build_wire


def write_csv(
    r_points,
    z_points,
    file_name="vessel_points.csv",
):
    """
    Writes the provided R and Z points to a CSV file.

    Parameters:
    R_points (list): The list of R points.
    Z_points (list): The list of Z points.
    file_name (str): The name of the CSV file to write to. Default is "vessel_points.csv".

    Returns:
    file_name (str): The name of the CSV file that was written to.
    """
    # Write the header and data
    with open(file_name, "w", encoding='utf-8', newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["X", "Y"])
        for r, z in zip(r_points, z_points):
            csv_writer.writerow([r, z])

    return file_name


def delete_csv_files(file_paths):
    """
    Deletes the CSV files at the provided file paths.

    Parameters:
    file_paths (list): The list of file paths to the CSV files to be deleted.

    Returns:
    None
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")  # Just to confirm it's done


def find_coil_centrepoint(
    vessel_height,
    vessel_radius,
    tf,
    x_offset=0.25,
    inner_coil=True,
    top=True,
):
    """
    Function to find the centrepoint of the coils to use the paramak PF coil generation script

    Returns:
        Tuple[float, float]: X, Y coordinates for the centrepoint of coil
    """
    # Using ternary operator for compactness
    vertical_offset = 0.0 if top else -0.0

    coil_height = vessel_height + vertical_offset

    # Calculate horizontal offset based on whether it's an inner or outer coil
    # Calculate coil radius based on whether it's an inner or outer coil
    coil_radius = x_offset if inner_coil else x_offset
    # Apply horizontal offset to the coil radius

    print("PF COIL RADIUS: ", coil_radius)

    # Shift to ensure no overlap with TF coils

    if inner_coil:
        if coil_radius <= 0.0:
            print("COIL TOO SMALL")

    # Shift vertically if coils sit above/below TF coils
    # TF_dr = 0.4

    # Elongation = 2 so double radii
    if coil_height <= (-2) * (vessel_radius + tf):
        coil_height = coil_height - (2 * tf)
    elif coil_height >= (2) * (vessel_radius + tf):
        coil_height = coil_height + (2 * tf)

    return coil_radius, coil_height


def generate_pf_coil_set(
    heights,
    x_offsets,
    vessel_radius,
    tf_dr,
    pf_dr,
    pf_dz,
    major_radius,
    inner_coil=False,
    top=True,
    pf_coil_path=None
):
    """
    Generates a set of Poloidal Field (PF) coils for a fusion reactor and returns cadquery objects.

    The function uses paramak to create PF coil geometries which are then exported to STEP files.
    These files are imported as cadquery objects and returned in a list, with cleanup of the
    STEP files performed afterwards.

    Parameters:
    - heights (list of float): Vertical positions for the coil centers.
    - x_offsets (list of float): Radial offsets for the coil centers from the vessel's major radius.
    - vessel_radius (float): Radius of the vessel.
    - major_radius (float): Major radius of the tokamak.
    - inner_coil (bool): Specifies if the coils are inner (True) or outer (False).
    - top (bool): Specifies if the coils are on the top (True) or bottom (False) of the vessel.

    Returns:
    - list of cadquery.Workplane: Cadquery objects representing the PF coils.
    """
    # COIL PARAMETERS (hardcoded for now)
    r_turns = 10
    z_turns = 10
    current_per_turn = 2

    # HEIGHT = 0.2
    # WIDTH = 0.2
    # Prepare lists for cadquery objects and STEP file paths
    cq_coils, step_files = [], []

    # Create PF coil objects and corresponding STEP files
    for count, height in enumerate(heights):
        centerpoint = find_coil_centrepoint(
            height,
            vessel_radius,
            tf_dr,
            x_offsets[count],
            inner_coil,
            top,
        )
        print(count)
        print(x_offsets[count])
        print("CENTER POINT")
        print(centerpoint, centerpoint[0])
        print("COIl NUM = ", count)
        print("COIL PROPERTIES:")
        height = pf_dz
        print(height, pf_dr, pf_dz)
        print(height, vessel_radius, major_radius,
              x_offsets[count], inner_coil, top)
        pf_coil = paramak.PoloidalFieldCoil(
            height=pf_dz, width=pf_dr, center_point=centerpoint, workplane="XY"
        )
        print(centerpoint)
        step_filename = f"pf_coil_{count}.step"
        pf_coil.export_stp(step_filename)
        step_files.append(step_filename)

    # Import the STEP files into cadquery objects and remove the files
    for step_file in step_files:
        cq_coils.append(cq.importers.importStep(step_file))
        os.remove(step_file)

        # After all coils are generated and before the function returns, add this:
    coil_data = []
    for count, height in enumerate(heights):
        centerpoint = find_coil_centrepoint(
            height,
            vessel_radius,
            tf_dr,
            x_offsets[count],
            inner_coil,
            top,
        )

        coil_x = 0
        coil_y = centerpoint[1]
        coil_z = 0
        coil_data.append(
            [
                r_turns,
                z_turns,
                current_per_turn,
                centerpoint[0],
                pf_dr,
                pf_dz,
                coil_x,
                coil_y,
                coil_z,
                0,
                1,
                0,
            ]
        )

    # Write coil data to CSV
    write_pf_coils_to_csv(coil_data, pf_coil_path)

    return cq_coils


def generate_pf_coil_from_array(coil_array):
    """
    Generates a set of Poloidal Field (PF) coils for a fusion reactor
    and returns a list of cadquery objects.
    """

    # Prepare lists for cadquery objects and STEP file paths
    pf_coils = []
    step_files = []
    cq_coils = []
    count = 0
    for coil in coil_array:
        count += 1
        pf_r, pf_z, pf_dr, pf_dz = coil
        centerpoint = (pf_r, pf_z)

        pf_coil = paramak.PoloidalFieldCoil(
            height=pf_dz, width=pf_dr, center_point=centerpoint, workplane="XY"
        )

        pf_coils.append(pf_coil)
        pf_coil = paramak.PoloidalFieldCoil(
            height=pf_dz, width=pf_dr, center_point=centerpoint, workplane="XY"
        )
        print(centerpoint)
        step_filename = f"pf_coil_{count}.step"
        pf_coil.export_stp(step_filename)
        step_files.append(step_filename)

    # Import the STEP files into cadquery objects and remove the files
    for step_file in step_files:
        cq_coils.append(cq.importers.importStep(step_file))
        os.remove(step_file)

    return cq_coils


def write_pf_coils_to_csv(coil_data, csv_file_path="pf_coils_1.csv"):
    """
    Writes or appends poloidal field(PF) coil data to a CSV file.

    Parameters:
    coil_data(list): The list of PF coil data to write to the CSV file.
    csv_file_path(str): The path to the CSV file to write to. Default is "pf_coils_1.csv".

    Returns:
    None
    """
    with open(csv_file_path, "a", newline="", encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(coil_data)
    print(f"PF Coil data appended to {csv_file_path}")


def create_tf_coils(R1, R2, thickness, distance, coil_num, tf_coil_path):
    """
    Creates a set of toroidal field (TF) coils for a fusion reactor.
    """

    tf_coils = paramak.ToroidalFieldCoilPrincetonD(
        R1=R1,
        R2=R2,
        thickness=thickness,
        distance=distance,
        number_of_coils=coil_num,
        with_inner_leg=True,
    )
    points = tf_coils.points

    with open(tf_coil_path, "w", newline="", encoding='utf-8') as file:
        # Create a CSV writer object
        writer = csv.writer(file)

        # Write the header row (optional)
        writer.writerow(["R", "Z", "Connection"])

        # Write each point as a row in the CSV file
        for point in points:
            writer.writerow(point)

    tf_coil_casing = paramak.TFCoilCasing(
        tf_coils,
        inner_offset=0.2,
        outer_offset=0.4,
        distance=0.2,
        vertical_section_offset=0.1,

    )
    tf_filename = "tf_coils.step"
    tf_casing_filename = "tf_coil_casing.step"
    tf_coil_casing.export_stp(tf_casing_filename)
    tf_coils.export_stp(tf_filename)

    tf_coils = cq.importers.importStep(tf_filename)
    tf_coil_casing = cq.importers.importStep(tf_casing_filename)

    os.remove(tf_filename)
    os.remove(tf_casing_filename)

    # rotate the tf_coils to be in correct position
    # tf_coils = tf_coils.rotate((0, 0, 0), (0, 1, 0), 180)

    return tf_coils, tf_coil_casing


def create_geometry(
    params: TokamakGeometryParams,
    tf_coil_path: str,
    pf_coil_path: str,
):
    """
    Generates a 3D model of a tokamak fusion reactor using the provided parameters.

    Parameters:
    - params (TokamakGeometryParams): Tokamak Geometry Parameters
    - tf_coil_path (str): Path to the CSV file for the toroidal field coils.
    - pf_coil_path (str): Path to the CSV file for the poloidal field coils.

    Returns:
    - list of cadquery.Workplane: Cadquery objects representing the tokamak components.
    """
    reactor_components = []

    # Accumulate and round off radii for precision
    accumulated_radii = list(accumulate(params.radial_build))
    accumulated_radii = [round(x, 2) for x in accumulated_radii]

    # Flag to identify the plasma component
    is_plasma = True

    major_radius = params.aspect_ratio * (accumulated_radii[0])
    print("PLASMA MINOR RAD : ", accumulated_radii[0])
    print("MAJOR RAD : ", major_radius)
    print("ASPECT RATIO : ", params.aspect_ratio)
    tokamak_component_list = []

    # Iterate over component radii and names to create toroidal components
    for minor_radius, component_name in zip(accumulated_radii, params.component_names):
        # Create a plasma torus for the first component
        print("Minor radius : ", minor_radius)
        if is_plasma:
            plasma_torus = Torus(
                r_0=major_radius, a=minor_radius, wire=False, degrees=FULL_REVOLVE
            )
            is_plasma = False  # Reset flag after creating plasma
            reactor_components.append(
                {"name": component_name, "component": plasma_torus.torus}
            )
            tokamak_component_list.append(plasma_torus.torus)
            layer_before = plasma_torus.torus
        else:
            # Create torus components for the remaining elements
            torus_component = Torus(
                r_0=major_radius, a=minor_radius, wire=False, degrees=FULL_REVOLVE
            )

            torus_to_append = torus_component.torus.cut(layer_before)
            tokamak_component_list.append(torus_to_append)
            layer_before = torus_component.torus

    print("tokamak component length after main components",
          len(tokamak_component_list))
    # Create TF coils and add them to the tokamak assembly
    tf_coils, tf_coil_casing = create_tf_coils(
        R1=1.1,
        R2=params.tf_radius,
        thickness=params.tf_dr,
        distance=params.tf_dz,
        coil_num=12,
        tf_coil_path=tf_coil_path,
    )

    # rotate the tf_coils to be positioned the same as the tokamak
    tf_coils = tf_coils.rotate((0, 0, 0), (1, 0, 0), 90)
    tf_coil_casing = tf_coil_casing.rotate((0, 0, 0), (1, 0, 0), 90)
    print("tokamak component length after TF", len(tokamak_component_list))

    tokamak_component_list.append(tf_coils)
    tokamak_component_list.append(tf_coil_casing)
    coil_set = generate_pf_coil_from_array(params.coils)
    print("length of coil set:", len(coil_set))
    # Append the coils to the tokamak_component_list
    for coil in coil_set:
        tokamak_component_list.append(coil)

    return tokamak_component_list
