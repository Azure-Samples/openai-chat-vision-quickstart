#!/usr/bin/env python3
import json


def fix_notebook(path):
    with open(path) as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            source = cell.get("source", [])
            new_source = []
            for line in source:
                # Fix: Add .rstrip("/") before + "/openai/v1/"
                line = line.replace(
                    '["AZURE_OPENAI_ENDPOINT"] + "/openai/v1/"', '["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1"'
                )
                new_source.append(line)
            cell["source"] = new_source

    with open(path, "w") as f:
        json.dump(nb, f, indent=1)
    print(f"Fixed {path}")


for nb_path in [
    "notebooks/chat_vision.ipynb",
    "notebooks/chat_pdf_images.ipynb",
    "notebooks/Spanish/chat_vision.ipynb",
    "notebooks/Spanish/chat_pdf_images.ipynb",
]:
    fix_notebook(nb_path)
