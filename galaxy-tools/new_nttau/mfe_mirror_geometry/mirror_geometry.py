"""
This module provides functions for creating a mirror reactor using
the CadQuery and Paramak libraries.

The module contains three main functions:

- `generate_coils`: Generates a list of CadQuery Workplane objects
    representing poloidal field coils.
- `create_hollow_cylinder`: Creates a hollow cylinder using CadQuery.
- `create_mirror_reactor`: Creates a mirror reactor using CadQuery.
"""
from dataclasses import dataclass
import os
import csv
import cadquery as cq
import paramak as pm


@dataclass
class PfCoil:
    """
    Attributes:
        radius (float): The radial position of the coil's center point from the origin.
        height (float): The vertical position of the coil's center point from the origin.
        dz (float): The full width (along the z-axis) of the coil.
        dr (float): The full height (along the radial direction) of the coil.
    """
    radius: float
    height: float
    dz: float
    dr: float


def export_pf_coils_to_csv(
        pf_coil_array: list[PfCoil],
        r_turns: int = 10,
        z_turns: int = 10,
        current_per_turn: float = 2,
        out_dir: str = "out",
        filename: str = "pf_coils.csv") -> None:
    """
    Export the PfCoil array to a CSV file.

    Args:
        pf_coil_array (List[PfCoil]): List of PfCoil objects to be exported.
        out_dir (str): Output directory for the CSV file. Default is "out".
        filename (str): Name of the CSV file. Default is "pf_coils.csv".
    """
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, filename)

    coil_x = 0
    coil_y = 0

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["R_turns", "Z_turns", "I (A)", "R_av",
                         "dr", "dz", "Coil_X", "Coil_Y", "Coil_Z", "Normal_x", "Normal_y", "Normal_z"])

        # Write the data
        for coil in pf_coil_array:
            writer.writerow([r_turns, z_turns, current_per_turn, coil.radius,
                            coil.dr, coil.dz, coil_x, coil_y, coil.height, 0, 0, 1])

    print(f"PF coils exported to {file_path}")


def generate_coils(pf_coil_array: list[PfCoil], out_dir: str = "out") -> list[cq.Workplane]:
    """
    Generate a list of CadQuery Workplane objects representing poloidal field coils.

    Args:
        pf_coil_array (List[PfCoil]): List of PfCoil objects containing
            the parameters for each poloidal field coil.
        out_dir (str): Output directory for the generated STEP files. Default is "out".

    Returns:
        List[cq.Workplane]: List of CadQuery Workplane objects representing the coils.
    """
    os.makedirs(out_dir, exist_ok=True)
    step_files = []
    cq_coils = []
    count = 0
    # Using the coil array to generate paramak coils
    for coil in pf_coil_array:
        count += 1
        centre_point = (coil.radius, coil.height)
        coil = pm.PoloidalFieldCoil(
            height=coil.dr,
            width=coil.dz,
            center_point=centre_point
        )
        coil.create_solid()

        step_filename = os.path.join(out_dir, f"pf_coil_{count}.step")
        coil.export_stp(step_filename)
        step_files.append(step_filename)

    # Import the STEP files into cadquery objects and remove the files
    for step_file in step_files:
        cq_coils.append(cq.importers.importStep(step_file))
        os.remove(step_file)
    return cq_coils


def create_hollow_cylinder(
        outer_height: float,
        outer_radius: float,
        inner_height: float,
        inner_radius: float) -> cq.Workplane:
    """
    Create a hollow cylinder using CadQuery.

    Args:
        outer_height (float): Height of the outer cylinder.
        outside_radius (float): Radius of the outer cylinder.
        inside_radius (float): Radius of the inner cylinder.
        inside_height (float): Height of the inner cylinder.

    Returns:
        cq.Workplane: CadQuery Workplane object representing the hollow cylinder.
    """
    # Create outer and inner cylinders
    outer_cylinder = cq.Workplane("XY").cylinder(outer_height, outer_radius)
    # Rotate by 10 degrees
    inner_cylinder = cq.Workplane("XY").cylinder(inner_height, inner_radius)
    # offset = outer_height - inside_height
    # inner_cylinder.translate((0, 15, 0))
    hollow_cylinder = outer_cylinder.cut(inner_cylinder)

    return hollow_cylinder


def cylinder_taper(
        total_height: float,
        top_radius: float,
        top_thickness: float,
        bottom_radius: float) -> cq.Workplane:
    """
    Create a plasma expander using CadQuery.

    Args:
        total_height (float): Total height of the plasma expander.
        top_radius (float): Radius of the top of the expander.
        top_thickness (float): Thickness of the top of the expander.
        bottom_radius (float): Radius of the bottom of the expander.
    Returns:
        cq.Workplane: CadQuery Workplane object representing the plasma expander.
    """
    # Create the 2D outline
    expander_profile = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .hLine(top_radius)  # Horizontal line to top radius
        .vLine(top_thickness)  # Vertical line to top thickness
        .threePointArc((bottom_radius + (top_radius - bottom_radius) / 2, total_height / 2),
                       (bottom_radius, total_height))  # Smooth arc to the bottom
        .hLine(-bottom_radius)  # Horizontal line to make the bottom flat
        .close()  # Close the shape to form a solid profile
    )

    # Revolve the outline 360 degrees as per your original intent
    plamsa_expander = expander_profile.revolve(360, (0, 0, 0), (0, 1, 0))

    return plamsa_expander


def end_cell_tapered(
        reactor_height: float,
        pinch_length: float,
        pinched_radius: float,
        pinch_thickness: float,
        mirror_plasma_rad: float) -> cq.Workplane:

    height_to_translate = reactor_height / 2 + pinch_length
    # Create the connection shape
    pinch = cylinder_taper(
        pinch_length,
        pinched_radius,
        pinch_thickness,
        mirror_plasma_rad
    )
    top_pinch = pinch.rotate((0, 0, 0), (1, 0, 0), 270)
    top_pinch = top_pinch.translate((0, 0, height_to_translate))

    bottom_pinch = pinch.rotate((0, 0, 0), (1, 0, 0), 90)
    bottom_pinch = bottom_pinch.translate((0, 0, -height_to_translate))
    return top_pinch.union(bottom_pinch), height_to_translate


def end_cell_cylinder(
        reactor_height: float,
        end_cell_radius: float,
        end_cell_length: float) -> cq.Workplane:
    """
    Create an end cell using CadQuery.

    Args:
        reactor_height (float): Height of the reactor.
        end_cell_radius (float): Radius of the end cell.
        end_cell_length (float): Length of the end cell.

    Returns:
        cq.Workplane: CadQuery Workplane object representing the end cell.
    """

    end_cell_pos = reactor_height / 2 + end_cell_length / 2
    end_cap = cq.Workplane("XY").cylinder(end_cell_length, end_cell_radius)
    top_end_cap = end_cap.translate((0, 0, end_cell_pos))
    bottom_end_cap = end_cap.translate((0, 0, -end_cell_pos))
    return top_end_cap.union(bottom_end_cap)


def plasma_expander(
        reactor_height: float,
        expander_length: float,
        expanded_radius: float,
        expander_thickness: float,
        pinched_radius: float) -> cq.Workplane:
    """
    Create a plasma expander using CadQuery.

    Args:
        reactor_height (float): Height of the reactor.
        pinch_length (float): Length of the pinch region.
        pinched_radius (float): Radius of the pinched region.
        pinch_thickness (float): Thickness of the pinched region.
        mirror_plasma_rad (float): Radius of the mirror plasma.

    Returns:
        cq.Workplane: CadQuery Workplane object representing the plasma expander.
    """
    height_to_translate = reactor_height + expander_length
    # Create the connection shape
    expander = cylinder_taper(
        expander_length,
        expanded_radius,
        expander_thickness,
        pinched_radius
    )
    top_expander = expander.rotate((0, 0, 0), (1, 0, 0), 270)
    top_expander = top_expander.translate((0, 0, height_to_translate))

    bottom_expander = expander.rotate((0, 0, 0), (1, 0, 0), 90)
    bottom_expander = bottom_expander.translate((0, 0, -height_to_translate))
    return top_expander.union(bottom_expander)


def generate_cylinder(radius: float, height: float) -> cq.Workplane:
    """
    Generate a cylinder using CadQuery.

    Args:
        radius (float): Radius of the cylinder.
        height (float): Height of the cylinder.

    Returns:
        cq.Workplane: CadQuery Workplane object representing the cylinder.
    """
    return cq.Workplane("XY").cylinder(height, radius)


def generate_radial_build_layers(
        radial_build: list[float],
        reactor_height: float,
        end_cell_rad: float
) -> None:
    """
    Generate each layer of a radial build individually for OpenMC simulations.

    Args:
        radial_build (list[float]): List of radial build values for each layer.
        layer_height (float): Height of the layers.
        output_directory (str): Directory to save the generated layers.

    Returns:
        radial_build_list: List of CadQuery Workplane objects
        representing the radial build layers.
    """
    # Define a bounding box (could be used for visualization or other purposes)
    radial_build_list = []
    total_radius = radial_build[0]
    previous_cylinder = generate_cylinder(total_radius, reactor_height)
    radial_build_list.append(previous_cylinder)
    end_cell_to_cut = generate_cylinder(end_cell_rad, reactor_height * 2)
    # radial_build_list.append(nbi)
    for i in range(1, len(radial_build)):
        total_radius += radial_build[i]
        thickness = total_radius - radial_build[0]
        height = reactor_height + 2 * thickness

        full_cylinder = generate_cylinder(total_radius, height)
        single_layer = full_cylinder.cut(previous_cylinder)

        single_layer = single_layer.cut(end_cell_to_cut)
        previous_cylinder = full_cylinder
        radial_build_list.append(single_layer)
    return radial_build_list, height


def create_nbi_cutter(nbi_radius: float, nbi_pos: float, nbi_offset: float, reactor_height: float, nbi_angle: float = 45) -> cq.Workplane:
    """
    Creates a neutral beam injection (NBI) cutter.

    Args:
        nbi_radius (float): Radius of the NBI cylinder.
        nbi_pos (float): Position offset for the NBI upper and lower cutters.
        nbi_offset (float): Offset to translate the second NBI cutter.
        reactor_height (float): Height of the reactor to determine the size of the cylinder.

    Returns:
        Any: A combined NBI cutter object.
    """
    nbi_cylinder = generate_cylinder(nbi_radius, reactor_height * 2)
    nbi_1 = nbi_cylinder.rotate((0, 0, 0), (1, 0, 0), nbi_angle)
    nbi_2 = nbi_cylinder.rotate((0, 0, 0), (1, 0, 0), -nbi_angle)
    nbi_2 = nbi_2.translate((0, 0, -nbi_offset))
    nbi = nbi_1.union(nbi_2)
    nbi_upper = nbi.translate((0, 0, nbi_pos))
    nbilower = nbi.translate((0, 0, -nbi_pos))
    nbi = nbi_upper.union(nbilower)
    return nbi


def create_ec_shield(reactor_height: float, end_cell_radius: float, end_cell_length: float, end_cell_thickness: float) -> cq.Workplane:
    """
    Creates an electron cyclotron (EC) shield.

    Args:
        reactor_height (float): Height of the reactor.
        end_cell_radius (float): Radius of the end cell.
        end_cell_length (float): Length of the end cell.
        end_cell_thickness (float): Thickness of the shield.

    Returns:
        Any: A combined EC shield object.
    """
    end_cell_pos = reactor_height / 2 + end_cell_length / 2
    end_cell = generate_cylinder(end_cell_radius, end_cell_length)
    shield = generate_cylinder(
        end_cell_radius + end_cell_thickness, end_cell_length)
    shield = shield.cut(end_cell)

    top_shield = shield.translate((0, 0, end_cell_pos))
    bottom_shield = shield.translate((0, 0, -end_cell_pos))
    shield = top_shield.union(bottom_shield)
    return shield
