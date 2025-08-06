import os
import yaml
import pynetbox

# ---- Configuration ----
NETBOX_URL = "http://localhost:8000"
NETBOX_TOKEN = "faf1b318bf1ae5ff6f5f2158b29392715fe8ebc9"  # Replace with your actual NetBox API token
DEVICE_TYPES_DIR = "device-types"
# -----------------------

# Initialize NetBox API connection
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

def get_or_create_manufacturer(name):
    slug = name.lower().replace(' ', '-')
    manufacturer = nb.dcim.manufacturers.get(slug=slug)
    if not manufacturer:
        manufacturer = nb.dcim.manufacturers.create({
            'name': name,
            'slug': slug
        })
        print(f"Created Manufacturer: {name}")
    return manufacturer

def import_device_type(manufacturer, data):
    slug = data.get('model', '').lower().replace(' ', '-')
    existing = nb.dcim.device_types.get(slug=slug, manufacturer_id=manufacturer.id)
    if existing:
        print(f"DeviceType already exists: {data.get('model')}")
        return existing

    payload = {
        "manufacturer": manufacturer.id,
        "model": data.get('model'),
        "slug": slug,
        "part_number": data.get('part_number', None),
        "u_height": data.get('u_height', 1),
        "is_full_depth": data.get('is_full_depth', True),
        "airflow": data.get('airflow', None),
        "comments": data.get('comments', '')
    }
    device_type = nb.dcim.device_types.create(payload)
    print(f"Imported DeviceType: {data.get('model')}")
    return device_type

def create_components(device_type, data):
    def bulk_create(endpoint, items, name_field='name'):
        for item in items:
            item['device_type'] = device_type.id
        if items:
            endpoint.create(items)
            print(f"Created {len(items)} {endpoint.name} for {device_type.model}")

    bulk_create(nb.dcim.interfaces, data.get('interfaces', []))
    bulk_create(nb.dcim.console_ports, data.get('console-ports', []))
    bulk_create(nb.dcim.console_server_ports, data.get('console-server-ports', []))
    bulk_create(nb.dcim.power_ports, data.get('power-ports', []))
    bulk_create(nb.dcim.power_outlets, data.get('power-outlets', []))
    bulk_create(nb.dcim.device_bays, data.get('device-bays', []))
    bulk_create(nb.dcim.module_bays, data.get('module-bays', []))

def main():
    for manufacturer_name in os.listdir(DEVICE_TYPES_DIR):
        manufacturer_path = os.path.join(DEVICE_TYPES_DIR, manufacturer_name)
        if os.path.isdir(manufacturer_path):
            manufacturer = get_or_create_manufacturer(manufacturer_name)
            for file_name in os.listdir(manufacturer_path):
                if file_name.endswith('.yaml') or file_name.endswith('.yml'):
                    file_path = os.path.join(manufacturer_path, file_name)
                    with open(file_path, 'r') as f:
                        try:
                            data = yaml.safe_load(f)
                            device_type = import_device_type(manufacturer, data)
                            if device_type:
                                create_components(device_type, data)
                        except Exception as e:
                            print(f"Failed to import {file_path}: {e}")

if __name__ == "__main__":
    main()
