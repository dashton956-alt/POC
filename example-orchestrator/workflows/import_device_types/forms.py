from orchestrator.forms import FormPage

class SelectVendorsForm(FormPage):
    class Config:
        title = "Select Vendor(s) to Import"

    selected_vendors: get_vendor_choices()
