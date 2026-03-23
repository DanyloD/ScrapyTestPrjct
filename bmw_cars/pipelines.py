# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import sqlite3
import re


class ScrapyfunDataValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        required_fields = ['model', 'name', 'registration']
        for field in required_fields:
            if not adapter.get(field) or adapter.get(field) == "N/A":
                spider.logger.warning(f"Dropping item: Missing required field '{field}'")
                raise DropItem(f"Missing required field: {field}")

        mileage = adapter.get('mileage')
        if mileage and mileage != "N/A":
            match = re.search(r'([\d,]+)\s*miles?', mileage, re.IGNORECASE)
            if match:
                 clean_mileage_str = match.group(1).replace(',', '')
                 adapter['mileage'] = int(clean_mileage_str)
            else:
                 first_word = mileage.split()[0]
                 clean_mileage_str = re.sub(r'[^\d]', '', first_word)
                 if clean_mileage_str:
                     adapter['mileage'] = int(clean_mileage_str)
                 else:
                     adapter['mileage'] = None

        range_val = adapter.get('range')
        if range_val and range_val != "N/A":
            match = re.search(r'([\d,]+)\s*miles?', range_val, re.IGNORECASE)
            if match:
                adapter['range'] = f"{match.group(1)} miles"
            else:
                first_word = range_val.split()[0]
                adapter['range'] = f"{first_word} miles" if first_word.isdigit() else range_val

        fuel = adapter.get('fuel')
        if fuel and fuel != "N/A":
            adapter['fuel'] = fuel.lower()

        for key, value in adapter.items():
            if value == "N/A":
                adapter[key] = None

        return item


class ScrapyfunSQLitePipeline:
    """
    Pipeline 2: Store data in SQLite database
    """
    def __init__(self):
        self.con = sqlite3.connect('bmw_cars.db')
        self.cur = self.con.cursor()
        self.create_table()

    def create_table(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            name TEXT NOT NULL,
            mileage INTEGER,
            registered TEXT,
            engine TEXT,
            range TEXT,
            exterior TEXT,
            fuel TEXT,
            transmission TEXT,
            registration TEXT UNIQUE NOT NULL,
            upholstery TEXT
        )
        """)
        self.con.commit()

    def process_item(self, item, spider):
        self.cur.execute("""
            INSERT OR IGNORE INTO cars (
                model, name, mileage, registered, 
                engine, range, exterior, fuel, transmission, 
                registration, upholstery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get('model'),
            item.get('name'),
            item.get('mileage'),
            item.get('registered'),
            item.get('engine'),
            item.get('range'),
            item.get('exterior'),
            item.get('fuel'),
            item.get('transmission'),
            item.get('registration'),
            item.get('upholstery')
        ))
        
        if self.cur.rowcount == 0:
             spider.logger.debug(f"Duplicate car ignored: {item.get('registration')}")
             
        self.con.commit()
        return item

    def close_spider(self, spider):
        self.con.close()
