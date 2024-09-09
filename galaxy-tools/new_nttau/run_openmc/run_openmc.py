"""
This script sets up and runs a Tritium Breeding Ratio (TBR) calculation using OpenMC.

The script performs the following tasks:
1. Parses input arguments to get the path to the input JSON file and the output directory.
2. Loads simulation parameters from the specified JSON file.
3. Sets up the simulation environment, including materials, geometry, and settings.
4. Runs the OpenMC simulation.
5. Moves output files to the specified output directory and removes any remaining temporary files.

Functions:
    load_json(file_path): Loads JSON data from a file.
    clear_directory(directory): Clears the contents of a directory.

Modules:
    - math: Provides access to mathematical functions.
    - os: Provides functions for interacting with the operating system.
    - numpy: Provides support for large, multi-dimensional arrays and matrices.
    - openmc: Provides functions for setting up and running Monte Carlo simulations of nuclear systems.
    - openmc_data_downloader: Extends the openmc.Materials class to allow nuclear data to be downloaded.
    - argparse: Provides a command-line argument parser.
    - json: Provides functions for parsing JSON data.
    - time: Provides time-related functions.

Usage:
    python script.py --input <input_json_file> --output <output_directory>

Arguments:
    --input: Path to the input JSON file containing simulation parameters. Default is 'input/default.json'.
    --output: Path to the output directory where results will be saved. Default is 'output'.

Example:
    python script.py --input input/simulation.json --output results
"""

import math
import os
import numpy as np
import openmc
import openmc_data_downloader  # extends the openmc.Materials class to allow data to be downloaded
import argparse
import json
import time

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
materials_dir = 'materials'
os.makedirs(materials_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

threads = sims["threads"]
mirror = sims["mirror"]
mirror_plasma_length = sims["mirror_plasma_length"]
tokamak = sims["tokamak"]
tokamak_plasma_radius = sims["tokamak_plasma_radius"]
stellarator = sims["stellarator"]
stellarator_plasma_radius = sims["stellarator_plasma_radius"]
mat_w_element = sims["mat_w_element"]
mat_w_density = sims["mat_w_density"]
mat_b_element = sims["mat_b_element"]
mat_b_density = sims["mat_b_density"]
batches = sims["batches"]
particles = sims["particles"]
x_max = sims["x_max"]
y_max = sims["y_max"]
z_max = sims["z_max"]

def clear_directory(directory):
    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
    else:
        os.makedirs(directory)

clear_directory(output_dir)


if sum([mirror, tokamak, stellarator]) != 1:
    raise ValueError("More than one reactor type is chosen/True") #makes sure only 1 reactor type is chosen


os.environ["OMP_NUM_THREADS"] = f"{threads}" # sets number of openmp threads to use

mat_p = openmc.Material(name="mat_p")
mat_p.add_element("H", 1, "ao")
mat_p.set_density("kg/m3", 0.01)


mat_w = openmc.Material(name="mat_w")
mat_w.add_element(f"{mat_w_element}", 1, "ao")
mat_w.set_density("g/cm3", mat_w_density)

mat_v = openmc.Material(name="mat_v")
mat_v.add_element("Fe", 1, "ao")
mat_v.set_density("kg/m3", 6.5e-27)

mat_b = openmc.Material(name="mat_b")
mat_b.add_elements_from_formula(f"{mat_b_element}")
mat_b.set_density("g/cm3", mat_b_density)






materials = openmc.Materials(
    [
        mat_p,
        mat_v,
        mat_w,
        mat_b
    ]
)

# downloads the nuclear data and sets the openmc_cross_sections environmental variable

materials.download_cross_section_data(
        libraries=["ENDFB-7.1-NNDC"],
        destination=materials_dir,
        set_OPENMC_CROSS_SECTIONS=True,
        particles=["neutron"],
    )

cross_sections_path = os.path.join(materials_dir, 'cross_sections.xml')
os.environ['OPENMC_CROSS_SECTIONS'] = cross_sections_path


# makes use of the dagmc geometry
dag_univ = openmc.DAGMCUniverse("dagmc.h5m")

# creates an edge of universe boundary surface
vac_surf = openmc.Sphere(r=10000, surface_id=9999, boundary_type="vacuum")

if tokamak == True:
    # adds reflective surface for the sector model at 0 degrees
    reflective_1 = openmc.Plane(
        a=math.sin(0),
        b=-math.cos(0),
        c=0.0,
        d=0.0,
        surface_id=9991,
        boundary_type="reflective",
    )

    # adds reflective surface for the sector model at 360 degrees
    reflective_2 = openmc.Plane(
        a=math.sin(math.radians(90)),
        b=-math.cos(math.radians(90)),
        c=0.0,
        d=0.0,
        surface_id=9990,
        boundary_type="reflective",
    )

    # specifies the region as below the universe boundary and inside the reflective surfaces
    region = -vac_surf & -reflective_1 & +reflective_2
else:
    region = -vac_surf

# creates a cell from the region and fills the cell with the dagmc geometry
containing_cell = openmc.Cell(cell_id=9999, region=region, fill=dag_univ)

geometry = openmc.Geometry(root=[containing_cell])

if mirror == True:
    settings = openmc.Settings()
    settings.batches = batches
    settings.particles = particles
    settings.output_dir = output_dir
    settings.run_mode = "fixed source"


    lower_left = [-10, -10, -mirror_plasma_length]
    upper_right = [10, 10, mirror_plasma_length]
    uniform_dist = openmc.stats.Box(lower_left, upper_right)
    my_source = openmc.Source(space=uniform_dist, domains=[mat_p])
    my_source.energy = openmc.stats.muir(e0=14080000.0, m_rat=5.0, kt=140000.0)
    my_source.angle = openmc.stats.Isotropic()


    settings.source = my_source

elif tokamak == True:
    # creates a simple isotropic neutron source in the center with 14MeV neutrons
    my_source = openmc.Source()
    # the distribution of radius is just a single value at the plasma major radius
    radius = openmc.stats.Discrete([tokamak_plasma_radius], [1])
    # the distribution of source z values is just a single value
    z_values = openmc.stats.Discrete([0], [1])
    # the distribution of source azimuthal angles values is a uniform distribution between 0 and 0.5 Pi
    # these angles must be the same as the reflective angles
    angle = openmc.stats.Uniform(a=0., b=math.radians(360))
    # this makes the ring source using the three distributions and a radius
    my_source.space = openmc.stats.CylindricalIndependent(r=radius, phi=angle, z=z_values, origin=(0.0, 0.0, 0.0))
    # sets the direction to isotropic
    my_source.angle = openmc.stats.Isotropic()
    # sets the energy distribution to a Muir distribution neutrons
    my_source.energy = openmc.stats.Muir(e0=14080000.0, m_rat=5.0, kt=20000.0)

    # specifies the simulation computational intensity
    settings = openmc.Settings()
    settings.batches = batches
    settings.particles = particles
    settings.output_dir = output_dir
    settings.inactive = 0
    settings.run_mode = "fixed source"
    settings.source = my_source

elif stellarator == True:
    settings = openmc.Settings()
    settings.batches = batches
    settings.particles = particles
    settings.output_dir = output_dir
    settings.run_mode = "fixed source"

    # creates a simple isotropic neutron source in the center with 14MeV neutrons
    # creates a simple isotropic neutron source in the center with 14MeV neutrons
    my_source = openmc.Source()
    # the distribution of radius is just a single value at the plasma major radius
    radius = openmc.stats.Discrete([stellarator_plasma_radius], [1])
    # the distribution of source z values is just a single value
    z_values = openmc.stats.Discrete([0], [1])
    # the distribution of source azimuthal angles values is a uniform distribution between 0 and 0.5 Pi
    # these angles must be the same as the reflective angles
    angle = openmc.stats.Uniform(a=0., b=math.radians(360))
    # this makes the ring source using the three distributions and a radius
    my_source.space = openmc.stats.CylindricalIndependent(r=radius, phi=angle, z=z_values, origin=(0.0, 0.0, 0.0)) 
    # sets the direction to isotropic
    my_source.angle = openmc.stats.Isotropic()
    # sets the energy distribution to a Muir distribution neutrons
    my_source.energy = openmc.stats.Muir(e0=14080000.0, m_rat=5.0, kt=20000.0)

    settings.source = my_source


# adds a tally to record the heat deposited in entire geometry
heating_cell_tally = openmc.Tally(name="heating")
heating_cell_tally.scores = ["heating"]

# adds a tally to record the total TBR
tbr_cell_tally = openmc.Tally(name="tbr")
tbr_cell_tally.scores = ["(n,Xt)"]

# creates a mesh that covers the geometry
mesh = openmc.RegularMesh()
mesh.dimension = [100, 100, 1000]
mesh.lower_left = [-110*x_max, -110*y_max, -110*z_max]  # x,y,z coordinates start at 0 as this is a sector model
mesh.upper_right = [110*x_max, 110*y_max, 110*z_max]
mesh_filter = openmc.MeshFilter(mesh) # creating a mesh

# makes a mesh tally using the previously created mesh and records heating on the mesh
heating_mesh_tally = openmc.Tally(name="heating_on_mesh")
heating_mesh_tally.filters = [mesh_filter]
heating_mesh_tally.scores = ["heating"]

# makes a mesh tally using the previously created mesh and records TBR on the mesh
tbr_mesh_tally = openmc.Tally(name="tbr_on_mesh")
tbr_mesh_tally.filters = [mesh_filter]
tbr_mesh_tally.scores = ["(n,Xt)"]

# groups the two tallies
tallies = openmc.Tallies([tbr_cell_tally, tbr_mesh_tally, heating_cell_tally, heating_mesh_tally])


# builds the openmc model
my_model = openmc.Model(
    materials=materials, geometry=geometry, settings=settings, tallies=tallies
)

# starts the simulation
my_model.run()

time.sleep(2)

for file in os.listdir('.'):
    if file.startswith('statepoint'):
        os.rename(file, os.path.join('statepoint_generic.h5'))