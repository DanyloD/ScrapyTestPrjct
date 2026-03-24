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
