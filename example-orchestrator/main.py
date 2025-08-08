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


from orchestrator import OrchestratorCore
from orchestrator.cli.main import app as core_cli
from orchestrator.settings import AppSettings
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from graphql_federation import CUSTOM_GRAPHQL_MODELS
from utils.system_status import get_system_status
import products  # noqa: F401  Side-effects
import workflows  # noqa: F401  Side-effects

app = OrchestratorCore(base_settings=AppSettings())
app.register_graphql(graphql_models=CUSTOM_GRAPHQL_MODELS)

# Add custom system status endpoint
status_router = APIRouter()

@status_router.get("/system-status")
async def system_status():
    """Get system status for Intent Based Orchestrator and NetBox."""
    return JSONResponse(get_system_status())

# Register the router
app.include_router(status_router, prefix="/api")

# Mount static files if directory exists
if os.path.exists("/home/orchestrator/static"):
    app.mount("/static", StaticFiles(directory="/home/orchestrator/static"), name="static")
app.register_graphql(graphql_models=CUSTOM_GRAPHQL_MODELS)

if __name__ == "__main__":
    core_cli()
