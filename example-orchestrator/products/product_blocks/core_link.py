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


from typing import Annotated

from annotated_types import Len
from orchestrator.domain.base import ProductBlockModel
from orchestrator.types import SI, SubscriptionLifecycle
from pydantic import computed_field

from products.product_blocks.core_port import CorePortBlock, CorePortBlockInactive, CorePortBlockProvisioning

ListOfPorts = Annotated[list[SI], Len(min_length=2, max_length=2)]


class CoreLinkBlockInactive(ProductBlockModel, product_block_name="CoreLink"):
    ports: ListOfPorts[CorePortBlockInactive]
    ims_id: int | None = None
    ipv6_prefix_ipam_id: int | None = None
    nrm_id: int | None = None
    under_maintenance: bool | None = None


class CoreLinkBlockProvisioning(CoreLinkBlockInactive, lifecycle=[SubscriptionLifecycle.PROVISIONING]):
    ports: ListOfPorts[CorePortBlockProvisioning]
    ims_id: int | None = None
    ipv6_prefix_ipam_id: int | None = None
    nrm_id: int | None = None
    under_maintenance: bool

    @computed_field  # type: ignore[misc]
    @property
    def title(self) -> str:
        return f"core link between {self.ports[0].node.node_name} and {self.ports[1].node.node_name}"


class CoreLinkBlock(CoreLinkBlockProvisioning, lifecycle=[SubscriptionLifecycle.ACTIVE]):
    ports: ListOfPorts[CorePortBlock]
    ims_id: int
    ipv6_prefix_ipam_id: int
    nrm_id: int
    under_maintenance: bool
