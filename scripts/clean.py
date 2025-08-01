# import os
# import subprocess

# def main():
#     print("🧹 Cleaning __pycache__...")
#     subprocess.run(["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-r", "{}", "+"])

#     print("🚀 CLEANED...")

# scripts/clean.py
import os
import shutil

def main():
    print("🧹 Cleaning __pycache__ folders...")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                print(f"Removing: {full_path}")
                shutil.rmtree(full_path, ignore_errors=True)
    print("✅ CLEANED.")
