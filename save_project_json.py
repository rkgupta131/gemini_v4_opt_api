import json
import os

def save_project(json_data, output_dir="generated_project"):

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    project = json_data["project"]
    files = project["files"]

    # --- Write all files into correct folders ---
    for path, content in files.items():
        full_path = os.path.join(output_dir, path)

        # Create folders automatically
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write file contents
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"\n Project saved to: {output_dir}")
    print(" You can now run:")
    print(f"cd {output_dir} && npm install && npm run dev")