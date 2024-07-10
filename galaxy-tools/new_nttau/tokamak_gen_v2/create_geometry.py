"""
This module is used to generate the geometry of a tokamak based on a given configuration file.

The module takes in three command-line arguments: the paths to the configuration file,
the toroidal field (TF) coil file, and the poloidal field (PF) coil file.

The configuration file is expected to be in JSON format
and contain a 'geometry' key with the following sub-keys:
'aspect_ratio', 'radial_build', 'component_names', 'TF_dz', 'TF_dr', 'PF_dr', 'PF_dz', 'With_Sol'.

The module reads the configuration file, extracts the geometry data, and assigns them to variables.
It then calculates the major radius and minor radius based on the aspect ratio and radial build.

The module also appends the coil data to the TF and PF coil files.
The coil data includes the number of turns in the R and Z directions and the current.

Dependencies:
- csv: for writing data to CSV files
- argparse: for parsing command-line arguments
- json: for parsing JSON files
- TokamakGen: for generating the tokamak geometry

Usage:
python3 create_geometry.py --input=INPUT_FILE --out_dir=OUT_DIR
"""

# pylint: disable=import-error
import argparse
import os
import zipfile

import cadquery as cq
from cq_utils import half_compound, save_bounding_box_to_csv
from files import clear_directory
from tokamakgen import create_geometry
from TokamakGeometryParams import load_params_json, save_params_json


def zip_directory(directory_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=directory_path)
                zipf.write(file_path, arcname)


def main(input_file: str, out_dir: str):
    params = load_params_json(input_file)

    # TODO these are not used
    # major_rad = aspect_ratio * radial_build[0]
    # max_a = sum(radial_build)
    # print(max)

    clear_directory(out_dir)

    tf_coil_path = os.path.join(out_dir, 'tf.csv')
    pf_coil_path = os.path.join(out_dir, 'pf.csv')

    reactor_components = create_geometry(params, tf_coil_path, pf_coil_path)

    # Create a directory for the .step files
    step_files_dir = os.path.join(out_dir, 'step_files')
    os.makedirs(step_files_dir, exist_ok=True)
    vals = []

    compound_object = None
    for i, component in enumerate(reactor_components):
        for o in component.all():
            vals.extend(o.vals())
        compound_object = cq.Compound.makeCompound(vals)
        current_object = reactor_components[i]
        # Use the name from component_names if it exists, otherwise use a default name
        if i < len(params.component_names):
            filename = params.component_names[i]
            print(filename)
        else:
            filename = f"component_{i - len(params.component_names)}"
            print(filename)

        # Save the .step file
        cq.exporters.export(current_object, os.path.join(
            step_files_dir, f"{filename}.step"))
        compound_object.exportStep(os.path.join(out_dir, 'compound.step'))

    save_bounding_box_to_csv(compound_object, out_dir, 'bounding_box.csv')

    # Create a Zip file and add all the .step files to it
    with zipfile.ZipFile(os.path.join(out_dir, 'constituent_files.zip'), 'w') as zipf:
        for file in os.listdir(step_files_dir):
            if file.endswith('.step'):
                zipf.write(os.path.join(step_files_dir, file))

    save_params_json(params, os.path.join(out_dir, 'used_input.json'))

    print("cutting")
    compound_half = half_compound(compound_object)
    print("object cut")
    cq.exporters.export(compound_half, os.path.join(out_dir, 'half_compound.step'))
    print("exported")
    
    zip_directory(out_dir, "tokamak_output_dir.zip")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Menard Tokamak geometry for configuration file.")
    parser.add_argument('--input', type=str,
                        default='input/R=3.json', help='Path to input JSON file')
    parser.add_argument('--out_dir', type=str, default='out', help='Path to output directory')
    args = parser.parse_args()

    main(args.input, args.out_dir)