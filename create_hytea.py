import os

folders = [
    "hytea/hytea_sdk",
    "hytea/hytea_components/rese",
    "hytea/hytea_components/electrolyser",
    "hytea/hytea_components/grid",
    "hytea/hytea_core",
    "hytea/data",
    "hytea/notebooks"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

py_folders = [
    "hytea/hytea_sdk",
    "hytea/hytea_components/rese",
    "hytea/hytea_components/electrolyser",
    "hytea/hytea_components/grid",
    "hytea/hytea_core"
]

for folder in py_folders:
    with open(os.path.join(folder, "__init__.py"), "w") as f:
        f.write("# init")

# Create placeholder files
placeholders = [
    "hytea/README.md",
    "hytea/pyproject.toml",
    "hytea/LICENSE",
    "hytea/.gitignore",
    "hytea/data/sample_wind_cf.csv",
    "hytea/notebooks/demo_colab.ipynb"
]

for file in placeholders:
    open(file, "w").close()

print("HyTEA folder structure created successfully!")
