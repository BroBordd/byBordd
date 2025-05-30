import os
import json
import re

def generate_mod_list(mods_folder_name="mods", output_file_name="mods.json"):
    """
    Scans the specified mods folder for Python files, extracts mod names,
    fancy names, versions, descriptions, API versions, and the base filename,
    and saves them to a JSON file.

    Args:
        mods_folder_name (str): The name of the folder containing the mod files.
                                Defaults to "mods".
        output_file_name (str): The name of the JSON file to create.
                                Defaults to "mods.json".
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mods_path = os.path.join(script_dir, mods_folder_name)
    output_path = os.path.join(script_dir, output_file_name)

    mod_list = []

    # Check if the mods folder exists
    if not os.path.isdir(mods_path):
        print(f"Error: The folder '{mods_path}' does not exist.")
        print("Please ensure 'modlist.py' is in the same directory as the 'mods' folder.")
        return

    print(f"Scanning mods in: {mods_path}")

    # Iterate through all files in the mods directory
    for filename in os.listdir(mods_path):
        if filename.endswith(".py"):
            filepath = os.path.join(mods_path, filename)
            
            mod_name = None
            mod_version = None
            mod_fancy_name = None
            mod_description = None
            api_version = None
            mod_filename_base = os.path.splitext(filename)[0] # Extract filename without extension
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # --- Extract Docstring Content (Mod Name, Version, Fancy Name, Description) ---
                docstring_full_match = re.search(r'"""\s*(.*?)\s*"""', content, re.DOTALL)
                
                if docstring_full_match:
                    docstring_content = docstring_full_match.group(1).strip()
                    lines = docstring_content.split('\n')
                    
                    title_line = None
                    for line in lines:
                        if line.strip():
                            title_line = line.strip()
                            break
                    
                    if title_line:
                        title_line_match = re.match(r'^(.*?)\s*v(\d+\.\d+)\s*(?:-\s*(.*))?$', title_line)
                        
                        if title_line_match:
                            mod_name = title_line_match.group(1).strip()
                            mod_version = title_line_match.group(2).strip()
                            mod_fancy_name = title_line_match.group(3).strip() if title_line_match.group(3) else "N/A"
                        else:
                            mod_name = title_line.strip()
                            mod_version = "N/A"
                            mod_fancy_name = "N/A"
                            print(f"Warning: Could not fully parse title line '{title_line}' in '{filename}'.")

                        description_lines = []
                        title_line_found = False
                        for line in lines:
                            if not title_line_found:
                                if line.strip() == title_line:
                                    title_line_found = True
                                continue
                            description_lines.append(line)
                        
                        mod_description = "\n".join(description_lines).strip()
                        if not mod_description:
                            mod_description = "No description provided."
                    else:
                        mod_name = mod_filename_base + " (Docstring Empty)"
                        mod_version = "N/A"
                        mod_fancy_name = "N/A"
                        mod_description = "No docstring found or docstring is empty."
                        print(f"Warning: Docstring empty or malformed in '{filename}'. Using fallback names/descriptions.")
                else:
                    mod_name = mod_filename_base + " (No Docstring)"
                    mod_version = "N/A"
                    mod_fancy_name = "N/A"
                    mod_description = "No docstring found."
                    print(f"Warning: No docstring found in '{filename}'. Using fallback names/descriptions.")

                # --- Extract API Version ---
                api_match = re.search(r'# ba_meta require api (\d+)', content)
                if api_match:
                    api_version = int(api_match.group(1))
                else:
                    api_version = "N/A"
                    print(f"Warning: Could not find API version in '{filename}'. Setting to 'N/A'.")

                mod_list.append({
                    "mod_name": mod_name,
                    "mod_fancy_name": mod_fancy_name,
                    "mod_version": mod_version,
                    "mod_description": mod_description,
                    "api_version": api_version,
                    "mod_filename_base": mod_filename_base # Added this field
                })

            except Exception as e:
                print(f"Error processing file '{filename}': {e}")
                print(f"Skipping '{filename}'.")
                continue

    # Write the collected data to a JSON file
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(mod_list, json_file, indent=4)
        print(f"\nSuccessfully created '{output_file_name}' at: {output_path}")
        print(f"Found {len(mod_list)} mods.")
    except Exception as e:
        print(f"Error writing to '{output_file_name}': {e}")

if __name__ == "__main__":
    generate_mod_list()
