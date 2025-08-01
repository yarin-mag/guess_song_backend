import os
import subprocess
import shutil

def remove_pycache():
    print("🧹 Cleaning __pycache__...")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                print(f"Removing {full_path}")
                shutil.rmtree(full_path, ignore_errors=True)

def main():
    remove_pycache()
    
    print("🚀 Starting FastAPI server...")
    subprocess.run([
        "uvicorn", "app.main:app",
        "--reload",
        "--reload-include", ".env"
    ])

if __name__ == "__main__":
    main()
