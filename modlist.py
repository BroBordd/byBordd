import os
import json
import re

def generate_mod_list(mods_folder_name="mods", output_file_name="mods.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mods_path = os.path.join(script_dir, mods_folder_name)
    output_path = os.path.join(script_dir, output_file_name)
    useful_mods = []
    useless_mods = []
    if not os.path.isdir(mods_path):
        print(f"Error: The folder '{mods_path}' does not exist.")
        print("Please ensure 'modlist.py' is in the same directory as the 'mods' folder.")
        return
    print(f"Scanning mods in: {mods_path}")
    for filename in os.listdir(mods_path):
        if filename.endswith(".py"):
            filepath = os.path.join(mods_path, filename)
            mod_name = None
            mod_version = None
            mod_fancy_name = None
            mod_description = None
            api_version = None
            mod_filename_base = os.path.splitext(filename)[0]
            is_useful = False
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if "# brobord collide grass" in content:
                    is_useful = True
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
                else:
                    mod_name = mod_filename_base + " (No Docstring)"
                    mod_version = "N/A"
                    mod_fancy_name = "N/A"
                    mod_description = "No docstring found."
                api_match = re.search(r'# ba_meta require api (\d+)', content)
                if api_match:
                    api_version = int(api_match.group(1))
                else:
                    api_version = "N/A"
                mod_info = {
                    "mod_name": mod_name,
                    "mod_fancy_name": mod_fancy_name,
                    "mod_version": mod_version,
                    "mod_description": mod_description,
                    "api_version": api_version,
                    "mod_filename_base": mod_filename_base
                }
                if is_useful:
                    useful_mods.append(mod_info)
                else:
                    useless_mods.append(mod_info)
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")
                continue
    useful_mods.sort(key=lambda x: x["mod_name"].lower())
    useless_mods.sort(key=lambda x: x["mod_name"].lower())
    mod_list = useful_mods + useless_mods
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(mod_list, json_file, indent=4)
        print(f"\nSuccessfully created '{output_file_name}' at: {output_path}")
        print(f"Found {len(useful_mods)} useful mods and {len(useless_mods)} useless mods.")
    except Exception as e:
        print(f"Error writing to '{output_file_name}': {e}")

if __name__ == "__main__":
    generate_mod_list()
