from orchestrator.workflow import workflow, init, step, done
from orchestrator.types import State
from orchestrator.targets import Target

from .forms import SelectVendorsForm

@step("Import NetBox Device Types for selected vendors")
def import_selected(state: State) -> State:
    selected = state["selected_vendors"]
    for vendor in selected:
        folder = os.path.join(DEVICE_TYPES_PATH, vendor)
        for fname in os.listdir(folder):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                fpath = os.path.join(folder, fname)
                # Load YAML, parse, send to NetBox (e.g. via pynetbox or API)
    return state

@workflow(
    "Import Device Types to NetBox",
    initial_input_form=SelectVendorsForm,
    target=Target.SYSTEM
)
def device_type_import_task() -> State:
    return init >> import_selected >> done
