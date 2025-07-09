from json import load, dump, JSONDecodeError
from os import path

def sort_mods(f_path="mods.json"):
    if not path.exists(f_path):
        print(f"Error: '{f_path}' not found.")
        return
    try:
        with open(f_path, 'r', encoding='utf-8') as f:
            d = load(f)
    except JSONDecodeError:
        print(f"Error: Invalid JSON in '{f_path}'.")
        return
    except Exception as e:
        print(f"Error reading '{f_path}': {e}")
        return
    if not isinstance(d, list):
        print(f"Error: Expected list in '{f_path}'.")
        return
    try:
        d.sort(key=lambda m: m.get("mod_name", "").lower())
    except TypeError as e:
        print(f"Error sorting: {e}")
        return
    try:
        with open(f_path, 'w', encoding='utf-8') as f:
            dump(d, f, indent=4, ensure_ascii=False)
        print(f"Sorted '{f_path}'.")
    except Exception as e:
        print(f"Error writing to '{f_path}': {e}")

if __name__ == "__main__":
    sort_mods("mods.json")
