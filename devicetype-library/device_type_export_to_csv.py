import os
import yaml
import csv

DEVICE_TYPES_DIR = 'device-types'
OUTPUT_CSV = 'device_types_inventory.csv'

device_types_data = []

for manufacturer_name in os.listdir(DEVICE_TYPES_DIR):
    manufacturer_dir = os.path.join(DEVICE_TYPES_DIR, manufacturer_name)
    if not os.path.isdir(manufacturer_dir):
        continue

    for filename in os.listdir(manufacturer_dir):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            filepath = os.path.join(manufacturer_dir, filename)
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            device_entry = {
                'Manufacturer': manufacturer_name,
                'Model': data.get('model', ''),
                'Part Number': data.get('part_number', ''),
                'Comments': data.get('comments', ''),
                'Interfaces': ', '.join([i.get('name', '') for i in data.get('interfaces', [])]),
                'Console Ports': ', '.join([c.get('name', '') for c in data.get('console-ports', [])]),
                'Power Ports': ', '.join([p.get('name', '') for p in data.get('power-ports', [])]),
                'Device Bays': ', '.join([d.get('name', '') for d in data.get('device-bays', [])])
            }

            device_types_data.append(device_entry)

# Write to CSV
with open(OUTPUT_CSV, 'w', newline='') as csvfile:
    fieldnames = ['Manufacturer', 'Model', 'Part Number', 'Comments', 'Interfaces', 'Console Ports', 'Power Ports', 'Device Bays']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for row in device_types_data:
        writer.writerow(row)

print(f"CSV Exported to {OUTPUT_CSV}")
