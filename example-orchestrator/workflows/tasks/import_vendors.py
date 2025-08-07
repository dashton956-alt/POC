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
from typing import Dict, List, Set, Tuple, Optional, TypeAlias, cast
from pydantic import Field, validator
from pydantic_forms.types import State
from orchestrator.forms import FormPage
from orchestrator.forms.validators import Choice, choice_list

# FORCE RELOAD - Updated at 2025-08-07 10:35:00
# This timestamp is used to force Python module reloading
import structlog
from orchestrator import workflow
from orchestrator.targets import Target
from orchestrator.workflow import StepList, done, init, step, conditional, identity

from services import netbox
from settings import settings

logger = structlog.get_logger(__name__)

# Path to the devicetype-library
DEVICETYPE_LIBRARY_PATH = Path("/home/orchestrator/devicetype-library")
DEVICE_TYPES_PATH = DEVICETYPE_LIBRARY_PATH / "device-types"


def get_available_vendors() -> List[str]:
    """
    Get list of available vendors from the devicetype-library.
    
    Returns:
        List of vendor names (directory names in device-types folder)
    """
    vendors = []
    if DEVICE_TYPES_PATH.exists():
        for vendor_dir in DEVICE_TYPES_PATH.iterdir():
            if vendor_dir.is_dir() and not vendor_dir.name.startswith('.'):
                vendors.append(vendor_dir.name)
    
    vendors.sort()
    logger.info("Found vendors in devicetype-library", count=len(vendors), vendors=vendors[:10])
    return vendors


def get_vendor_choices():
    """Get vendor choices for the form."""
    logger.info("=== GET VENDOR CHOICES CALLED ===")
    logger.info("Device types path", path=str(DEVICE_TYPES_PATH), exists=DEVICE_TYPES_PATH.exists())
    
    try:
        vendors = []
        if DEVICE_TYPES_PATH.exists():
            vendors = sorted([
                name for name in os.listdir(DEVICE_TYPES_PATH)
                if (DEVICE_TYPES_PATH / name).is_dir() and not name.startswith('.')
            ])
            logger.info("Found vendors", count=len(vendors), vendors=vendors[:10])
        else:
            logger.warning("Device types path does not exist", path=str(DEVICE_TYPES_PATH))
    except Exception as e:
        logger.error("Failed to get vendor choices", error=str(e), path=str(DEVICE_TYPES_PATH))
        vendors = []
    
    # Add "All" option at the beginning - FIXED: Include all vendors, not just first 10
    choices = [("all", "All Vendors")] + [(vendor, vendor) for vendor in vendors]
    logger.info("Created vendor choices", count=len(choices), total_vendors=len(vendors))
    
    # Return Choice object for single selection dropdown
    return Choice("VendorEnum", choices)


# Define the TypeAlias for the vendor choice
VendorChoice: TypeAlias = cast(type[Choice], get_vendor_choices())


# Simple form using orchestrator form system
class VendorImportForm(FormPage):
    class Config:
        title = "Import Vendors to NetBox"
        description = "Select vendors to import from devicetype-library into NetBox (supports multiple selection)"
    
    # Multi-select vendor field - unlimited selection
    selected_vendors: List[str] = Field(
        default=["all"], 
        description="Select vendors to import (choose 'all' for all vendors, or select multiple specific vendors)"
    )


def vendor_import_form_generator():
    """Generate the input form for vendor import workflow."""
    
    logger.info("=== FORM GENERATOR CALLED ===")
    # Return the static form class
    return VendorImportForm


def get_vendor_device_types(vendor: str) -> List[Dict]:
    """
    Get all device types for a specific vendor.
    
    Args:
        vendor: Vendor name
        
    Returns:
        List of device type dictionaries
    """
    vendor_path = DEVICE_TYPES_PATH / vendor
    device_types = []
    
    if not vendor_path.exists():
        logger.warning("Vendor path not found", vendor=vendor, path=str(vendor_path))
        return device_types
    
    for device_file in vendor_path.glob("*.yaml"):
        try:
            with open(device_file, 'r', encoding='utf-8') as f:
                device_data = yaml.safe_load(f)
                if device_data:
                    device_types.append(device_data)
        except Exception as e:
            logger.warning("Failed to load device type file", 
                         file=str(device_file), error=str(e))
    
    # Also check for .yml files
    for device_file in vendor_path.glob("*.yml"):
        try:
            with open(device_file, 'r', encoding='utf-8') as f:
                device_data = yaml.safe_load(f)
                if device_data:
                    device_types.append(device_data)
        except Exception as e:
            logger.warning("Failed to load device type file", 
                         file=str(device_file), error=str(e))
    
    logger.info("Loaded device types for vendor", 
                vendor=vendor, count=len(device_types))
    return device_types


def check_vendor_exists_in_netbox(vendor_name: str, vendor_slug: str) -> bool:
    """
    Check if a vendor (manufacturer) already exists in NetBox.
    
    Args:
        vendor_name: Vendor display name
        vendor_slug: Vendor slug
        
    Returns:
        True if vendor exists, False otherwise
    """
    try:
        # Check by slug first (more reliable)
        existing = netbox.api.dcim.manufacturers.get(slug=vendor_slug)
        if existing:
            return True
        
        # Check by name as fallback
        existing = netbox.api.dcim.manufacturers.get(name=vendor_name)
        if existing:
            return True
            
        return False
    except Exception as e:
        logger.warning("Error checking vendor existence", 
                      vendor=vendor_name, error=str(e))
        return False


def create_vendor_slug(vendor_name: str) -> str:
    """
    Create a NetBox-compatible slug from vendor name.
    
    Args:
        vendor_name: Original vendor name
        
    Returns:
        Slug-compatible string
    """
    # Replace spaces and special characters with hyphens
    slug = vendor_name.lower()
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


@step("Check devicetype-library availability")
def check_devicetype_library() -> State:
    """Check if devicetype-library is available and accessible."""
    library_status = {
        "library_path": str(DEVICETYPE_LIBRARY_PATH),
        "device_types_path": str(DEVICE_TYPES_PATH),
        "library_exists": DEVICETYPE_LIBRARY_PATH.exists(),
        "device_types_exists": DEVICE_TYPES_PATH.exists(),
        "vendor_count": 0,
        "available_vendors": []
    }
    
    if not DEVICETYPE_LIBRARY_PATH.exists():
        logger.error("Devicetype-library not found", path=str(DEVICETYPE_LIBRARY_PATH))
        return {"library_status": library_status, "error": "Devicetype-library not found"}
    
    if not DEVICE_TYPES_PATH.exists():
        logger.error("Device-types directory not found", path=str(DEVICE_TYPES_PATH))
        return {"library_status": library_status, "error": "Device-types directory not found"}
    
    available_vendors = get_available_vendors()
    library_status.update({
        "vendor_count": len(available_vendors),
        "available_vendors": available_vendors
    })
    
    logger.info("Devicetype-library check complete", 
                vendor_count=len(available_vendors))
    
    return {"library_status": library_status}


@step("Get existing vendors from NetBox")
def get_existing_vendors() -> State:
    """Get list of existing manufacturers/vendors in NetBox."""
    existing_vendors = []
    existing_slugs = set()
    
    try:
        manufacturers = netbox.api.dcim.manufacturers.all()
        for manufacturer in manufacturers:
            vendor_info = {
                "id": manufacturer.id,
                "name": manufacturer.name,
                "slug": manufacturer.slug
            }
            existing_vendors.append(vendor_info)
            existing_slugs.add(manufacturer.slug)
        
        logger.info("Retrieved existing vendors from NetBox", count=len(existing_vendors))
        
    except Exception as e:
        logger.error("Failed to retrieve existing vendors", error=str(e))
        return {"error": f"Failed to retrieve existing vendors: {str(e)}"}
    
    return {
        "existing_vendors": existing_vendors,
        "existing_slugs": list(existing_slugs),
        "existing_vendor_count": len(existing_vendors)
    }


@step("Analyze vendors for import")
def analyze_vendors_for_import(state: State) -> State:
    """Analyze which vendors need to be imported."""
    library_status = state.get("library_status", {})
    existing_slugs = set(state.get("existing_slugs", []))
    available_vendors = library_status.get("available_vendors", [])
    
    # Get selected vendors from form
    selected_vendors_from_form = state.get("selected_vendors", ["all"])
    
    logger.info("=== ANALYZE VENDORS FOR IMPORT ===")
    logger.info("Selected vendors from form", selected_vendors=selected_vendors_from_form)
    logger.info("Available vendors count", count=len(available_vendors))
    
    # Process form input into a list
    if isinstance(selected_vendors_from_form, list):
        selected_vendors_list = selected_vendors_from_form
    elif isinstance(selected_vendors_from_form, str):
        selected_vendors_list = [selected_vendors_from_form]
    else:
        selected_vendors_list = ["all"]
    
    # Filter vendors based on selection
    if "all" in selected_vendors_list:
        vendors_to_process = available_vendors
        logger.info("Processing ALL vendors", count=len(vendors_to_process))
    else:
        # Filter for specific vendors (case-insensitive matching)
        vendors_to_process = []
        for vendor in available_vendors:
            for selected_vendor in selected_vendors_list:
                if (vendor.lower() == selected_vendor.lower() or 
                    selected_vendor.lower() in vendor.lower() or 
                    vendor.lower() in selected_vendor.lower()):
                    if vendor not in vendors_to_process:  # Avoid duplicates
                        vendors_to_process.append(vendor)
                    break
        
        logger.info("Processing SELECTED vendors", 
                   selected=selected_vendors_list,
                   matched_count=len(vendors_to_process),
                   matched_vendors=vendors_to_process)
    
    vendors_to_import = []
    vendors_existing = []
    vendors_with_issues = []
    
    for vendor_name in vendors_to_process:
        vendor_slug = create_vendor_slug(vendor_name)
        
        # Check if vendor already exists
        if vendor_slug in existing_slugs:
            vendors_existing.append({
                "name": vendor_name,
                "slug": vendor_slug,
                "reason": "Already exists"
            })
            continue
        
        # Check if we can load device types for this vendor
        device_types = get_vendor_device_types(vendor_name)
        if not device_types:
            vendors_with_issues.append({
                "name": vendor_name,
                "slug": vendor_slug,
                "reason": "No device types found"
            })
            continue
        
        vendors_to_import.append({
            "name": vendor_name,
            "slug": vendor_slug,
            "device_type_count": len(device_types)
        })
    
    analysis = {
        "vendors_to_import": vendors_to_import,
        "vendors_existing": vendors_existing,
        "vendors_with_issues": vendors_with_issues,
        "import_count": len(vendors_to_import),
        "existing_count": len(vendors_existing),
        "issues_count": len(vendors_with_issues),
        "selected_vendors": selected_vendors_list,
        "execution_mode": "selective_import"
    }
    
    logger.info("Vendor analysis complete",
                selected=selected_vendors_list,
                to_import=len(vendors_to_import),
                existing=len(vendors_existing),
                issues=len(vendors_with_issues))
    
    return {"vendor_analysis": analysis}


@step("Import vendors into NetBox")
def import_vendors(state: State) -> State:
    """Import vendors directly into NetBox."""
    vendor_analysis = state.get("vendor_analysis", {})
    vendors_to_import = vendor_analysis.get("vendors_to_import", [])
    
    logger.info("=== IMPORT VENDORS DEBUG ===")
    logger.info("Vendors to import count", count=len(vendors_to_import))
    logger.info("Vendor details", vendors=vendors_to_import)
    logger.info("*** LIVE IMPORT MODE - VENDORS WILL BE CREATED IN NETBOX ***")
    
    if len(vendors_to_import) == 0:
        logger.warning("No vendors to import! Check vendor analysis step.")
        return {"import_results": {
            "imported_vendors": [],
            "import_errors": [],
            "success_count": 0,
            "error_count": 0
        }}
    
    imported_vendors = []
    import_errors = []
    
    for vendor_info in vendors_to_import:
        vendor_name = vendor_info["name"]
        vendor_slug = vendor_info["slug"]
        
        logger.info("Attempting to import vendor", name=vendor_name, slug=vendor_slug)
        
        try:
            # Create manufacturer payload
            logger.info("Creating manufacturer payload", name=vendor_name, slug=vendor_slug)
            manufacturer_payload = netbox.ManufacturerPayload(
                name=vendor_name,
                slug=vendor_slug
            )
            
            # Create in NetBox
            logger.info("Calling netbox.create()", payload=str(manufacturer_payload))
            result = netbox.create(manufacturer_payload)
            logger.info("NetBox create result", result=str(result), type=type(result))
            
            imported_vendors.append({
                "name": vendor_name,
                "slug": vendor_slug,
                "device_type_count": vendor_info.get("device_type_count", 0),
                "netbox_id": result.id if hasattr(result, 'id') else None
            })
            
            logger.info("Successfully imported vendor",
                       vendor=vendor_name, slug=vendor_slug, result_id=getattr(result, 'id', None))
            
        except Exception as e:
            logger.error("Exception during vendor import", 
                        vendor=vendor_name, 
                        error=str(e), 
                        error_type=type(e).__name__)
            
            error_info = {
                "name": vendor_name,
                "slug": vendor_slug,
                "error": str(e)
            }
            import_errors.append(error_info)
    
    import_results = {
        "imported_vendors": imported_vendors,
        "import_errors": import_errors,
        "success_count": len(imported_vendors),
        "error_count": len(import_errors)
    }
    
    logger.info("Vendor import complete",
                successful=len(imported_vendors),
                errors=len(import_errors))
    
    return {"import_results": import_results}


@step("Generate import summary")
def generate_import_summary(state: State) -> State:
    """Generate a comprehensive summary of the import operation."""
    library_status = state.get("library_status", {})
    vendor_analysis = state.get("vendor_analysis", {})
    import_results = state.get("import_results", {})
    
    # Get selected vendors from analysis
    selected_vendors = vendor_analysis.get("selected_vendors", ["all"])
    
    summary = {
        "execution_mode": {
            "selected_vendors": selected_vendors,
            "selection_type": "all" if "all" in selected_vendors else "specific"
        },
        "library_info": {
            "total_vendors_available": library_status.get("vendor_count", 0),
            "library_path": library_status.get("library_path", ""),
        },
        "analysis_results": {
            "vendors_to_import": vendor_analysis.get("import_count", 0),
            "vendors_already_existing": vendor_analysis.get("existing_count", 0),
            "vendors_with_issues": vendor_analysis.get("issues_count", 0),
        },
        "import_results": {
            "successfully_imported": import_results.get("success_count", 0),
            "import_errors": import_results.get("error_count", 0),
        },
        "imported_vendor_details": import_results.get("imported_vendors", []),
        "error_details": import_results.get("import_errors", [])
    }
    
    # Log summary
    logger.info("=== VENDOR IMPORT SUMMARY ===")
    logger.info(f"Selected vendors: {selected_vendors}")
    logger.info(f"Selection type: {'All vendors' if 'all' in selected_vendors else 'Specific vendors'}")
    logger.info(f"Total vendors in library: {summary['library_info']['total_vendors_available']}")
    logger.info(f"Vendors to import: {summary['analysis_results']['vendors_to_import']}")
    logger.info(f"Vendors already existing: {summary['analysis_results']['vendors_already_existing']}")
    logger.info(f"Vendors with issues: {summary['analysis_results']['vendors_with_issues']}")
    logger.info(f"Successfully imported: {summary['import_results']['successfully_imported']}")
    logger.info(f"Import errors: {summary['import_results']['import_errors']}")
    logger.info("===============================")
    
    return {"import_summary": summary}


# Deployment confirmation form for dry run results
class DeployConfirmationForm(FormPage):
    class Config:
        title = "Deploy Vendor Import"
        description = "Select vendor to deploy to NetBox (run dry run first to preview)"
    
    # Use the same vendor choice as the main form
    selected_vendors: VendorChoice = "all"  # type: ignore
    deploy_confirmed: bool = Field(default=False, description="Deploy the selected vendor to NetBox")


def deploy_confirmation_form_generator(state: State):
    """Generate deployment confirmation form with vendor selection."""
    logger.info("=== DEPLOY CONFIRMATION FORM GENERATOR ===")
    return DeployConfirmationForm


@step("Deploy vendors to NetBox")
def deploy_vendors_to_netbox(state: State) -> State:
    """Deploy the selected vendors to NetBox after confirmation."""
    # Get deployment confirmation from form
    deploy_confirmed = state.get("deploy_confirmed", False)
    selected_vendors_from_form = state.get("selected_vendors", "all")
    
    logger.info("=== DEPLOYMENT STEP ===")
    logger.info("Deploy confirmation", deploy_confirmed=deploy_confirmed)
    logger.info("Selected vendor for deployment", selected_vendor=selected_vendors_from_form)
    
    if not deploy_confirmed:
        logger.info("Deployment not confirmed - stopping without changes")
        return {
            "deployment_results": {
                "deployed": False,
                "reason": "User did not confirm deployment",
                "vendors_deployed": 0
            }
        }
    
    # Handle vendor selection
    if isinstance(selected_vendors_from_form, list) and len(selected_vendors_from_form) > 0:
        selected_vendor = selected_vendors_from_form[0]
    else:
        selected_vendor = selected_vendors_from_form if isinstance(selected_vendors_from_form, str) else "all"
    
    # Get available vendors from library
    available_vendors = get_available_vendors()
    
    # Filter vendors based on selection
    if selected_vendor != "all":
        filtered_vendors = []
        for vendor in available_vendors:
            if (vendor.lower() == selected_vendor.lower() or 
                selected_vendor.lower() in vendor.lower() or 
                vendor.lower() in selected_vendor.lower()):
                filtered_vendors.append(vendor)
        available_vendors = filtered_vendors
    
    if not available_vendors:
        logger.warning("No vendors to deploy", selected_vendor=selected_vendor)
        return {
            "deployment_results": {
                "deployed": False,
                "reason": f"No vendors matched selection: {selected_vendor}",
                "vendors_deployed": 0
            }
        }
    
    logger.info("*** DEPLOYING VENDORS TO NETBOX ***")
    logger.info("Vendors to deploy", count=len(available_vendors), vendors=available_vendors)
    
    # Deploy each vendor
    deployed_vendors = []
    deployment_errors = []
    existing_vendors = []
    
    for vendor_name in available_vendors:
        vendor_slug = create_vendor_slug(vendor_name)
        
        try:
            # Check if vendor already exists
            if check_vendor_exists_in_netbox(vendor_name, vendor_slug):
                logger.info("Vendor already exists, skipping", vendor=vendor_name)
                existing_vendors.append({
                    "name": vendor_name,
                    "slug": vendor_slug,
                    "reason": "Already exists"
                })
                continue
            
            # Check if we have device types for this vendor
            device_types = get_vendor_device_types(vendor_name)
            if not device_types:
                logger.warning("No device types found for vendor", vendor=vendor_name)
                deployment_errors.append({
                    "vendor": vendor_name,
                    "error": "No device types found in devicetype-library"
                })
                continue
            
            # Create vendor in NetBox
            vendor_data = {
                "name": vendor_name,
                "slug": vendor_slug,
                "description": f"Imported from devicetype-library"
            }
            
            response = netbox.api.dcim.manufacturers.create(vendor_data)
            logger.info("Successfully deployed vendor", vendor=vendor_name, slug=vendor_slug, id=response.id)
            
            deployed_vendors.append({
                "name": vendor_name,
                "slug": vendor_slug,
                "dry_run": False,
                "netbox_id": response.id,
                "device_type_count": len(device_types)
            })
                
        except Exception as e:
            logger.error("Failed to deploy vendor", vendor=vendor_name, error=str(e))
            deployment_errors.append({
                "vendor": vendor_name,
                "error": str(e)
            })
    
    deployment_results = {
        "deployed": True,
        "vendors_deployed": len(deployed_vendors),
        "vendors_already_existing": len(existing_vendors),
        "deployment_errors": len(deployment_errors),
        "deployed_vendor_details": deployed_vendors,
        "existing_vendor_details": existing_vendors,
        "error_details": deployment_errors,
        "selected_vendor": selected_vendor
    }
    
    logger.info("=== DEPLOYMENT COMPLETE ===")
    logger.info("Successfully deployed", count=len(deployed_vendors))
    logger.info("Already existing", count=len(existing_vendors))
    logger.info("Deployment errors", count=len(deployment_errors))
    
    return {"deployment_results": deployment_results}


@workflow("Import Vendors to NetBox", target=Target.SYSTEM, initial_input_form=vendor_import_form_generator)
def task_import_vendors() -> StepList:
    """
    Import vendors from devicetype-library into NetBox with vendor selection.
    
    Features:
    - Select specific vendors or import all (unlimited multi-select)
    - Direct import to NetBox (no dry run)
    - Supports multiple vendor selection
    """
    return (
        init
        >> check_devicetype_library
        >> get_existing_vendors
        >> analyze_vendors_for_import
        >> import_vendors  # Direct import to NetBox
        >> generate_import_summary  # Provides import results summary
        >> done
    )


# NOTE: Deployment workflow removed since we're doing direct imports now
# @workflow("Deploy Dry Run Results to NetBox", target=Target.SYSTEM, initial_input_form=deploy_confirmation_form_generator)
# def task_deploy_vendors() -> StepList:
#     """
#     Separate workflow to deploy vendors to NetBox.
#     
#     This workflow allows you to deploy vendors after reviewing a dry run, 
#     or directly deploy specific vendors to NetBox.
#     """
#     return (
#         init
#         >> deploy_vendors_to_netbox
#         >> done
#     )


# Standalone functions for direct usage
def import_specific_vendors(vendor_names: List[str]) -> Dict:
    """
    Import specific vendors by name.
    
    Args:
        vendor_names: List of vendor names to import
        
    Returns:
        Dictionary with import results
    """
    results = {
        "requested_vendors": vendor_names,
        "imported": [],
        "skipped": [],
        "errors": []
    }
    
    available_vendors = get_available_vendors()
    
    for vendor_name in vendor_names:
        if vendor_name not in available_vendors:
            results["errors"].append({
                "vendor": vendor_name,
                "error": "Vendor not found in devicetype-library"
            })
            continue
        
        vendor_slug = create_vendor_slug(vendor_name)
        
        # Check if already exists
        if check_vendor_exists_in_netbox(vendor_name, vendor_slug):
            results["skipped"].append({
                "vendor": vendor_name,
                "reason": "Already exists in NetBox"
            })
            continue
        
        try:
            manufacturer_payload = netbox.ManufacturerPayload(
                name=vendor_name,
                slug=vendor_slug
            )
            netbox.create(manufacturer_payload)
            
            results["imported"].append({
                "vendor": vendor_name,
                "slug": vendor_slug
            })
            
        except Exception as e:
            results["errors"].append({
                "vendor": vendor_name,
                "error": str(e)
            })
    
    return results


def get_vendor_statistics() -> Dict:
    """
    Get statistics about vendors in devicetype-library vs NetBox.
    
    Returns:
        Dictionary with vendor statistics
    """
    available_vendors = get_available_vendors()
    
    try:
        existing_manufacturers = netbox.api.dcim.manufacturers.all()
        existing_vendor_names = {m.name for m in existing_manufacturers}
        existing_vendor_slugs = {m.slug for m in existing_manufacturers}
    except Exception as e:
        logger.error("Failed to get existing manufacturers", error=str(e))
        return {"error": str(e)}
    
    stats = {
        "library_vendors": len(available_vendors),
        "netbox_vendors": len(existing_manufacturers),
        "vendors_in_both": 0,
        "vendors_only_in_library": [],
        "vendors_only_in_netbox": list(existing_vendor_names),
        "matching_vendors": []
    }
    
    for vendor in available_vendors:
        vendor_slug = create_vendor_slug(vendor)
        
        if vendor in existing_vendor_names or vendor_slug in existing_vendor_slugs:
            stats["vendors_in_both"] += 1
            stats["matching_vendors"].append(vendor)
            if vendor in stats["vendors_only_in_netbox"]:
                stats["vendors_only_in_netbox"].remove(vendor)
        else:
            stats["vendors_only_in_library"].append(vendor)
    
    return stats


if __name__ == "__main__":
    # For testing purposes
    print("Vendor Import Script")
    print("===================")
    
    # Get statistics
    stats = get_vendor_statistics()
    if "error" not in stats:
        print(f"Vendors in library: {stats['library_vendors']}")
        print(f"Vendors in NetBox: {stats['netbox_vendors']}")
        print(f"Vendors in both: {stats['vendors_in_both']}")
        print(f"Vendors only in library: {len(stats['vendors_only_in_library'])}")
        print(f"Vendors only in NetBox: {len(stats['vendors_only_in_netbox'])}")
    else:
        print(f"Error getting statistics: {stats['error']}")
