import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for src_path in [
    os.path.join(repo_root, "backend"),
    os.path.join(repo_root, "data-collection", "src"),
    os.path.join(repo_root, "data-quality"),
    os.path.join(repo_root, "data-quality", "src"),
    os.path.join(repo_root, "statistical-engine", "src"),
    os.path.join(repo_root, "intelligence", "src"),
]:
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
