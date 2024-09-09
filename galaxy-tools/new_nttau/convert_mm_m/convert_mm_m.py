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

convert_step_units_to_meters("Vacuum.step")
convert_step_units_to_meters("First_Wall.step")
convert_step_units_to_meters("Plasma.step")
convert_step_units_to_meters("Blanket.step")