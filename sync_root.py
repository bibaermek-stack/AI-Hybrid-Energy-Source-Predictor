import os
import shutil

src_dir = "EcoPredict AI"
dst_dir = "."

skip = {".git", ".venv", "__pycache__", "build", ".idea", ".vscode", "modified_labels.csv", "sync_root.py"}

for item in os.listdir(src_dir):
    if item in skip:
        continue
    s = os.path.join(src_dir, item)
    d = os.path.join(dst_dir, item)
    if os.path.isdir(s):
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(s, d, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "build", "modified_labels.csv"))
    else:
        shutil.copy2(s, d)

print("SUCCESS: Workspace root fully synchronized with EcoPredict AI!")
