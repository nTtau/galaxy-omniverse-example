"""
This module contains functions for manipulating 3D compounds using the CadQuery library.

Functions:
generate_cross_section(compound_to_cut: cq.Compound) -> cq.Compound:
    Generate a cross section of a given compound.

half_compound(compound_to_cut: cq.Compound) -> cq.Compound:
    Halves a given compound along a specified direction.
"""
import cadquery as cq
import os
import csv
from typing import Union


def get_volume(obj: cq.Workplane) -> float:
    """
    Get the volume of a CadQuery object.
    """
    return obj.val().Volume()


def convert_step_units_to_meters(file_path):
    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Replace the specific string
    content = content.replace('SI_UNIT(.MILLI.,.METRE.)', 'SI_UNIT(.METRE.)')

    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.write(content)

    print("Conversion complete. File updated.")


def generate_cross_section(compound_to_cut: cq.Compound) -> cq.Compound:
    """
    Generate a cross section of a given compound.

    This function creates a cross section by intersecting
    the compound with a box that spans the X-Y plane and
    intersects the center height of the compound's bounding box.

    Parameters:
    compound_to_cut (cq.Compound): The compound to generate a cross section of.

    Returns:
    cq.Compound: The cross section of the compound.
    """
    # Get the bounding box of the compound
    bbox = compound_to_cut.BoundingBox()
    # Get the center of the bounding box
    center = bbox.center
    # Create a box that spans the X-Y plane and intersects the center height
    box = cq.Workplane().box(bbox.xlen * 2, bbox.ylen * 2, 0.01,
                             centered=(True, True, False)).translate((0, 0, center.z)).val()
    # Create a section of the compound by intersecting with the box
    section = compound_to_cut.intersect(box)
    return section


def half_compound(compound_to_cut: cq.Compound) -> cq.Compound:
    """
    Halves a given compound along a specified direction.

    This function creates a half of the compound 
    by intersecting the compound with a box that spans 
    the entire compound in the specified direction.

    Parameters:
    compound (cq.Compound): The compound to halve.

    Returns:
    cq.Compound: The halved compound.
    """
    # Get the bounding box of the compound
    bbox = compound_to_cut.BoundingBox()
    # Get the center of the bounding box
    center = bbox.center
    # Create a thin box along the Y-Z plane at the center of the X-axis
    splitter = cq.Workplane().box(0.01, bbox.ylen * 2, bbox.zlen * 2,
                                  centered=(True, True, True)).translate((center.x, 0, 0)).val()
    # Initialize an empty list to store the half solids
    half_solids = []
    # Iterate over the solids in the compound
    for solid in compound_to_cut.Solids():
        # Split each solid using the splitter box
        split_result = solid.split(splitter)
        # Get the solids from the split result
        solids = split_result.Solids()
        # Append the first half solid to the list
        half_solids.append(solids[0])
    # Create a new compound from the half solids
    result_halved = cq.Compound.makeCompound(half_solids)
    return result_halved


def create_compound(components: list[cq.Solid]) -> cq.Compound:
    """
    Create a CadQuery Compound object from a list of CadQuery Solid objects.

    This function takes a list of CadQuery Solid objects, extracts the underlying geometric values 
    from each Solid, and combines them into a single Compound object.

    Args:
        components (list[cq.Solid]): List of CadQuery Solid objects.

    Returns:
        cq.Compound: CadQuery Compound object 
        containing the combined geometric values of all input Solids.
    """
    vals = []
    for component in components:
        for sub_solid in component.all():
            vals.extend(sub_solid.vals())
        compound_object = cq.Compound.makeCompound(vals)
    return compound_object


def export_step_from_list(components: list[cq.Solid], out_dir: str, filenames: list[str] = None):
    """
    Export a list of CadQuery Solid objects to an output directory.

    Args:
        components (list[cq.Solid]): List of CadQuery Solid objects to export.
        out_dir (str): Output directory for the STEP file.
        filename (str): Name of the STEP file to create.
    """
    if filenames is not None and len(filenames) != len(components):
        raise ValueError(
            "Number of filenames should match the number of components")
    if filenames is None:
        filenames = [f"component_{i}" for i in range(len(components))]
    # Print length of components
    print(f"Number of components: {len(components)}")
    for i, component in enumerate(components):
        cq.exporters.export(component, os.path.join(
            out_dir, f"{filenames[i]}.step"))


def print_bounding_box(cadquery_compound: Union[cq.Workplane, cq.Compound]):
    # Get the bounding box of the compound
    bounding_box = cadquery_compound.BoundingBox()

    # Extracting the bounds
    x_min, y_min, z_min = bounding_box.xmin, bounding_box.ymin, bounding_box.zmin
    x_max, y_max, z_max = bounding_box.xmax, bounding_box.ymax, bounding_box.zmax

    # Printing the bounding box coordinates
    print(f"Bounding Box:\n"
          f"X: {x_min} to {x_max}\n"
          f"Y: {y_min} to {y_max}\n"
          f"Z: {z_min} to {z_max}")


def save_bounding_box_to_csv(
        cadquery_compound: Union[cq.Workplane, cq.Compound],
        output_directory: str = 'out',
        output_filename: str = 'bounding_box.csv') -> None:
    """
    Saves the bounding box dimensions of a CadQuery compound to a CSV file.

    Args:
        cadquery_compound (Union[cq.Workplane, cq.Compound]): The CadQuery compound object.
        output_directory (str): The directory where the CSV file will be saved. Defaults to 'out'.

    Returns:
        None
    """
    os.makedirs(output_directory, exist_ok=True)

    # Define the full path for the CSV file
    file_path = os.path.join(output_directory, output_filename)

    # Get the bounding box of the compound
    bounding_box = cadquery_compound.BoundingBox()

    # Extracting the bounds
    x_min, y_min, z_min = bounding_box.xmin, bounding_box.ymin, bounding_box.zmin
    x_max, y_max, z_max = bounding_box.xmax, bounding_box.ymax, bounding_box.zmax

    # Writing the bounding box coordinates to a CSV file
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Axis", "Min", "Max"])
        writer.writerow(["X", x_min, x_max])
        writer.writerow(["Y", y_min, y_max])
        writer.writerow(["Z", z_min, z_max])
