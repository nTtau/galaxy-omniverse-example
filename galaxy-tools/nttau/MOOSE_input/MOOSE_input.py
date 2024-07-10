import argparse
import json

# Set up argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
file_path = args.file_path

# Load JSON data from the provided file path
with open(file_path, 'r') as file:
    data = json.load(file)

# Extract the mesh file name from the JSON data
inputs = data['inputs']
heating = data["heating"]
heat_source = data["heat_source"]
specific_heats = data["specific_heats"]
densities = data["densities"]
conductivities = data["conductivities"]

mesh_file = inputs['mesh_file'] 
material = inputs["material"]
sim_time = inputs["sim_time"]
time_step = inputs["time_step"]
num_layers = inputs["num_layers"]
reactor_model = inputs["reactor_model"]

heating_status = heating["heating_status"]
heating_function = heating["heating_function"]
heating_block = heating["heating_block"]

heat_source_status = heat_source["heat_source_status"]
heat_factor = heat_source["heat_factor"]
heat_function = heat_source["heat_function"]

specific_heat_1 = specific_heats["specific_heat_1"]
specific_heat_2 = specific_heats["specific_heat_2"]
specific_heat_3 = specific_heats["specific_heat_3"]
specific_heat_4 = specific_heats["specific_heat_4"]
specific_heat_5 = specific_heats["specific_heat_5"]

density_1 = densities["density_1"]
density_2 = densities["density_2"]
density_3 = densities["density_3"]
density_4 = densities["density_4"]
density_5 = densities["density_5"]

conductivity_1 = conductivities["conductivity_1"]
conductivity_2 = conductivities["conductivity_2"]
conductivity_3 = conductivities["conductivity_3"]
conductivity_4 = conductivities["conductivity_4"]
conductivity_5 = conductivities["conductivity_5"]


# Additional content to add to the .i file
content_mesh = f"""
[Mesh]
  file = reactor.msh
[]
"""

content_variables = """
[Variables]
  [T]
    initial_condition = 300
  []
[]
"""

content_kernels = """
[Kernels]
  [heat_conduction]
    type = HeatConduction
    variable = T
  []
  [time_derivative]
    type = SpecificHeatConductionTimeDerivative
    variable = T
  []"""


if heat_source_status == True:
  source_kernel = f"""  
  [heat_source]
    type = HeatSource
    variable = T
    value = {heat_factor}
    function = '{heat_function}'
  []
[]
"""
elif heat_source_status == False:
   source_kernel = """
[]
"""

# Start the materials content with the header
content_materials = """
[Materials]"""


for i in range(1, num_layers + 1):
    # Access each property using the 'eval' function to get the variable's value by name
    specific_heat_var_name = f"specific_heat_{i}"
    density_var_name = f"density_{i}"
    conductivity_var_name = f"conductivity_{i}"

    if reactor_model.lower() == "sphere":
      heating_boundary = f"sph_{heating_block}_sphere"
      material_block = f"sph_{i}_volume"
    elif reactor_model.lower() == "cylinder":
      heating_boundary = f"cyl_{heating_block}_wall"
      material_block = f"cyl_{i}_vol"
    
    # Get the actual variable values
    specific_heat_value = eval(specific_heat_var_name)
    density_value = eval(density_var_name)
    conductivity_value = eval(conductivity_var_name)

    content_materials += f"""
# Material definitions for boundary {i}
  [specific_heat_{30 + i}]
  type = ParsedMaterial
  block = {30 + i}
  f_name = 'specific_heat'
  args = 'T'
  function = '{specific_heat_value}'  # Actual function for boundary {i}
  []

  [density_{30 + i}]
  type = GenericConstantMaterial
  block = {30 + i}
  prop_names = 'density'
  prop_values = '{density_value}'  # Actual density for boundary {i}
  []

  [thermal_conductivity_{30 + i}]
  type = GenericConstantMaterial
  block = {30 + i}
  prop_names = 'thermal_conductivity'
  prop_values = '{conductivity_value}'  # Actual thermal conductivity for boundary {i}
  []"""

content_materials += """
[]
"""


if heating_status:
  content_heating = f"""
[BCs]
  [heating]
    type = FunctionDirichletBC
    variable = T
    function = '{heating_function}'
    boundary = '{heating_boundary}'
  []
[]
"""
else:
  content_heating = ""


content_preconditioning = """
[Preconditioning]
  [smp]
    type = SMP
    full = true
  []
[]
"""

content_executioner = f"""
[Executioner]
  type = Transient
  solve_type = NEWTON
  start_time = 0.0
  end_time = {sim_time}
  dt = {time_step}
[]
"""

content_outputs = """
[Outputs]
  exodus = true
[]
"""

new_content = content_mesh + content_variables + content_kernels + source_kernel + content_materials + content_heating + content_preconditioning + content_executioner + content_outputs

filename = "your_file.i"

def append_to_i_file(filename, new_content):
    with open(filename, 'w') as file:
        file.write(new_content)
    print(f"Content added to {filename} successfully.")

append_to_i_file(filename, new_content)


