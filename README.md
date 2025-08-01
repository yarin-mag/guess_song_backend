If First time running / installation: 
    Windows PC:
        python -m venv .venv
        ./.venv/Scripts/Activate.ps1
        python scripts/clean.py
        python .\scripts\run_api.py

Second time+ Running:
    Windows PC:
        ./.venv/Scripts/Activate.ps1
        python .\scripts\clean.py
        python .\scripts\run_api.py

Debug:
    Just F5 but notice to do it from the root of the project where you see backend and frontend folders.
    Or just fine tune the launch.json if you open only backend project.
