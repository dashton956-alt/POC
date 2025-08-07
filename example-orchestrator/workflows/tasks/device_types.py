# Copyright 2019-2023 SURF.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from pydantic_forms.types import State
import structlog
from orchestrator import workflow
from orchestrator.targets import Target
from orchestrator.workflow import StepList, done, init, step

from services import netbox
from settings import settings

logger = structlog.get_logger(__name__)

# Path to the devicetype-library
DEVICETYPE_LIBRARY_PATH = Path(__file__).parent.parent.parent.parent / "devicetype-library"
DEVICE_TYPES_PATH = DEVICETYPE_LIBRARY_PATH / "device-types"


def get_available_device_types() -> List[Tuple[str, str]]:
    """
    Get list of available device types from the devicetype-library.
    
    Returns:
        List of (vendor, device_type) tuples
    """
    device_types = []
    if DEVICE_TYPES_PATH.exists():
        for vendor_dir in DEVICE_TYPES_PATH.iterdir():
            if vendor_dir.is_dir() and not vendor_dir.name.startswith('.'):
                # Get YAML files for this vendor
                for device_file in vendor_dir.glob("*.yaml"):
                    device_types.append((vendor_dir.name, device_file.stem))
                for device_file in vendor_dir.glob("*.yml"):
                    device_types.append((vendor_dir.name, device_file.stem))
    
    device_types.sort()
    logger.info("Found device types in devicetype-library", count=len(device_types))
    return device_types


def load_device_type_definition(vendor: str, device_type: str) -> Optional[Dict]:
    """Load device type definition from YAML file."""
    device_file = DEVICE_TYPES_PATH / vendor / f"{device_type}.yaml"
    if not device_file.exists():
        device_file = DEVICE_TYPES_PATH / vendor / f"{device_type}.yml"
    
    if not device_file.exists():
        return None
    
    try:
        with open(device_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load device type {vendor}/{device_type}: {e}")
        return None


def create_manufacturer_slug(manufacturer_name: str) -> str:
    """Create NetBox-compatible slug from manufacturer name."""
    slug = manufacturer_name.lower()
    slug = slug.replace(' ', '-')
    slug = slug.replace('&', 'and')
    slug = slug.replace('.', '')
    slug = slug.replace(',', '')
    slug = slug.replace('(', '')
    slug = slug.replace(')', '')
    slug = slug.replace('/', '-')
    slug = slug.replace('\\', '-')
    
    # Remove multiple consecutive hyphens
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


@step("Analyze available device types")
def analyze_device_types() -> State:
    """Analyze available device types from devicetype-library."""
    device_types = get_available_device_types()
    
    # Group by vendor
    vendors = {}
    for vendor, device_type in device_types:
        if vendor not in vendors:
            vendors[vendor] = []
        vendors[vendor].append(device_type)
    
    analysis = {
        "total_device_types": len(device_types),
        "total_vendors": len(vendors),
        "vendors": vendors,
        "top_vendors": sorted(
            [(v, len(dt)) for v, dt in vendors.items()], 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
    }
    
    logger.info(
        "Device type analysis complete",
        total_device_types=analysis["total_device_types"],
        total_vendors=analysis["total_vendors"],
        top_vendors=[f"{v}({c})" for v, c in analysis["top_vendors"][:5]]
    )
    
    return {"analysis": analysis}


@step("Import device types from devicetype-library")
def import_device_types(state: State) -> State:
    """Import device types from devicetype-library into NetBox."""
    analysis = state["analysis"]
    device_types = get_available_device_types()
    
    # Limit import for safety - can be configured
    max_imports = getattr(settings, 'MAX_DEVICE_TYPE_IMPORTS', 100)
    if len(device_types) > max_imports:
        device_types = device_types[:max_imports]
        logger.warning(f"Limiting import to {max_imports} device types")
    
    imported_count = 0
    skipped_count = 0
    failed_count = 0
    imported_details = []
    failed_details = []
    
    # Get existing manufacturers
    existing_manufacturers = {}
    try:
        manufacturers = netbox.api.dcim.manufacturers.all()
        for manufacturer in manufacturers:
            existing_manufacturers[manufacturer.slug] = manufacturer
    except Exception as e:
        logger.error(f"Failed to get existing manufacturers: {e}")
    
    # Get existing device types
    existing_device_types = set()
    try:
        device_type_objects = netbox.api.dcim.device_types.all()
        for dt in device_type_objects:
            key = f"{dt.manufacturer.slug}_{dt.slug}"
            existing_device_types.add(key)
    except Exception as e:
        logger.error(f"Failed to get existing device types: {e}")
    
    for vendor, device_type in device_types:
        try:
            # Load device type definition
            definition = load_device_type_definition(vendor, device_type)
            if not definition:
                failed_count += 1
                failed_details.append({
                    "vendor": vendor,
                    "device_type": device_type,
                    "error": "Could not load device type definition"
                })
                continue
            
            # Create manufacturer slug
            manufacturer_slug = create_manufacturer_slug(vendor)
            device_slug = definition.get('slug', device_type.lower().replace(' ', '-'))
            device_key = f"{manufacturer_slug}_{device_slug}"
            
            # Check if device type already exists
            if device_key in existing_device_types:
                skipped_count += 1
                continue
            
            # Ensure manufacturer exists
            manufacturer = None
            if manufacturer_slug in existing_manufacturers:
                manufacturer = existing_manufacturers[manufacturer_slug]
            else:
                # Create manufacturer
                try:
                    manufacturer_data = netbox.ManufacturerPayload(
                        name=vendor,
                        slug=manufacturer_slug
                    )
                    manufacturer = netbox.create(manufacturer_data)
                    existing_manufacturers[manufacturer_slug] = manufacturer
                    logger.info(f"Created manufacturer: {vendor}")
                except Exception as e:
                    failed_count += 1
                    failed_details.append({
                        "vendor": vendor,
                        "device_type": device_type,
                        "error": f"Failed to create manufacturer: {e}"
                    })
                    continue
            
            # Create device type
            model = definition.get('model', device_type)
            
            device_type_data = netbox.DeviceTypePayload(
                manufacturer=manufacturer,
                model=model,
                slug=device_slug,
                u_height=definition.get('u_height', 1),
                is_full_depth=definition.get('is_full_depth', True)
            )
            
            created_device_type = netbox.create(device_type_data)
            imported_count += 1
            imported_details.append({
                "vendor": vendor,
                "device_type": device_type,
                "model": model,
                "slug": device_slug,
                "id": created_device_type.id if hasattr(created_device_type, 'id') else None
            })
            
            # Add to existing set to avoid duplicates in this run
            existing_device_types.add(device_key)
            
            logger.info(f"Imported device type: {vendor}/{model}")
            
        except Exception as e:
            failed_count += 1
            failed_details.append({
                "vendor": vendor,
                "device_type": device_type,
                "error": str(e)
            })
            logger.error(f"Failed to import device type {vendor}/{device_type}: {e}")
    
    result = {
        "total_processed": len(device_types),
        "imported": imported_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "imported_details": imported_details,
        "failed_details": failed_details[:10]  # Limit failed details
    }
    
    logger.info(
        "Device type import complete",
        total_processed=result["total_processed"],
        imported=result["imported"],
        skipped=result["skipped"],
        failed=result["failed"]
    )
    
    return {"import_result": result}


@workflow("Import Device Types", target=Target.SYSTEM)
def task_import_device_types() -> StepList:
    return init >> analyze_device_types >> import_device_types >> done
