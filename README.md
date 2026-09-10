# AM Wire — Crypto Morning Intelligence

Static morning dashboard. The Python agent writes `data/latest-report.json` and copies it to `frontend/data/latest-report.json` for the site.

## Run the agent (Step 2)

From the project root:

```bash
py -3 -m pip install -r requirements.txt
py -3 agent/run.py
```

## Run the dashboard

From the `frontend` folder:

```bash
py -3 -m http.server 8080
```

Open http://localhost:8080

Do not open `index.html` as a file. The browser cannot load the JSON over `file://`.
