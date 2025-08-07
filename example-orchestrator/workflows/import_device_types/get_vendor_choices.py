import os
from orchestrator.forms.validators import Choice, choice_list

DEVICE_TYPES_PATH = "/opt/devicetype-library/device-types"  # Adjust as needed

def get_vendor_choices():
    try:
        vendors = sorted([
            name for name in os.listdir(DEVICE_TYPES_PATH)
            if os.path.isdir(os.path.join(DEVICE_TYPES_PATH, name))
        ])
    except FileNotFoundError:
        vendors = []

    return choice_list(
        Choice("VendorEnum", zip(vendors, vendors)),
        min_items=1,
        max_items=len(vendors),
        unique_items=True
    )
