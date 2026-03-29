# How to run

If you are using `uv` as your package manager:

1. Sync and install the required dependencies (if not already installed):
```bash
uv sync
uv run playwright install chromium
```

2. Run the spider from the root folder of the project:
```bash
uv run scrapy crawl bmw_used
```

After the execution is complete, all data will be automatically saved in the `bmw_cars.db` file.

Example of 'bmw_cars.db' file
<img width="2656" height="692" alt="CleanShot 2026-03-29 at 19 56 17@2x" src="https://github.com/user-attachments/assets/c38905f7-0fda-498e-9fa6-1222e10c55cb" />
