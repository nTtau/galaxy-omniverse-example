import openmc
import time
import json
import argparse
import os

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Set up argument parser
parser = argparse.ArgumentParser(description="Create OpenMC TBR calculations.")
parser.add_argument('--input', type=str, default='input/default.json', help='Path to input JSON file')
parser.add_argument('--output', type=str, default='output', help='Path to output directory')

# Parse the arguments
args = parser.parse_args()

# Load the JSON file
sims = load_json(args.input)

output_dir = 'out'

batches = sims["batches"]

# open the results file
sp = openmc.StatePoint(f"statepoint.h5")

# access the TBR tally using pandas dataframes
tbr_cell_tally = sp.get_tally(name="tbr")

# print cell tally for the TBR
print(f"The reactor has a TBR of {tbr_cell_tally.mean.sum()}")
print(f"Standard deviation on the TBR is {tbr_cell_tally.std_dev.sum()}")

# extracts the mesh tally result
tbr_mesh_tally = sp.get_tally(name="tbr_on_mesh")

# gets the mesh used for the tally
mesh = tbr_mesh_tally.find_filter(openmc.MeshFilter).mesh

# writes the TBR mesh tally as a vtk file
mesh.write_data_to_vtk(
    filename="tritium_production_map.vtk",
    datasets={"mean": tbr_mesh_tally.mean}  # the first "mean" is the name of the data set label inside the vtk file
)

# access the heating tally using pandas dataframes
heating_cell_tally = sp.get_tally(name="heating")

# print cell tally results with unit conversion
# raw tally result is multipled by 4 as this is a sector model of 1/4 of the total model (90 degrees from 360)
# raw tally result is divided by 1e6 to convert the standard units of eV to MeV
print(f"The heating of {4*heating_cell_tally.mean.sum()/1e6} MeV per source particle is deposited")
print(f"Standard deviation on the heating tally is {heating_cell_tally.std_dev.sum()}")

# extracts the mesh tally result
heating_mesh_tally = sp.get_tally(name="heating_on_mesh")

# gets the mesh used for the tally
mesh = heating_mesh_tally.find_filter(openmc.MeshFilter).mesh

# writes the TBR mesh tally as a vtk file
mesh.write_data_to_vtk(
    filename="heating_map.vtk",
    datasets={"mean": heating_mesh_tally.mean}  # the first "mean" is the name of the data set label inside the vtk file
)

time.sleep(2)

for file in os.listdir('.'):
    if file.endswith('.vtk'):
        os.rename(file, os.path.join(output_dir, file))

for file in os.listdir('.'):
    if file.endswith('.vtk'):
        os.unlink(file) #moves files to output folder and removes from parent