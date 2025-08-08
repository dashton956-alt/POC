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


from orchestrator.workflows import LazyWorkflowInstance

# Original workflows
LazyWorkflowInstance("workflows.node.create_node", "create_node")
LazyWorkflowInstance("workflows.node.modify_node", "modify_node")
LazyWorkflowInstance("workflows.node.modify_sync_ports", "modify_sync_ports")
LazyWorkflowInstance("workflows.node.terminate_node", "terminate_node")
LazyWorkflowInstance("workflows.node.validate_node", "validate_node")

LazyWorkflowInstance("workflows.port.create_port", "create_port")
LazyWorkflowInstance("workflows.port.modify_port", "modify_port")
LazyWorkflowInstance("workflows.port.terminate_port", "terminate_port")
LazyWorkflowInstance("workflows.port.validate_port", "validate_port")

LazyWorkflowInstance("workflows.core_link.create_core_link", "create_core_link")
LazyWorkflowInstance("workflows.core_link.modify_core_link", "modify_core_link")
LazyWorkflowInstance("workflows.core_link.terminate_core_link", "terminate_core_link")
LazyWorkflowInstance("workflows.core_link.validate_core_link", "validate_core_link")

LazyWorkflowInstance("workflows.l2vpn.create_l2vpn", "create_l2vpn")
LazyWorkflowInstance("workflows.l2vpn.modify_l2vpn", "modify_l2vpn")
LazyWorkflowInstance("workflows.l2vpn.terminate_l2vpn", "terminate_l2vpn")
LazyWorkflowInstance("workflows.l2vpn.validate_l2vpn", "validate_l2vpn")

LazyWorkflowInstance("workflows.tasks.bootstrap_netbox", "task_bootstrap_netbox")
LazyWorkflowInstance("workflows.tasks.wipe_netbox", "task_wipe_netbox")
LazyWorkflowInstance("workflows.tasks.import_vendors", "task_import_vendors")
LazyWorkflowInstance("workflows.tasks.device_types", "task_import_device_types")

# Network Automation Workflows - Operations Group
LazyWorkflowInstance("workflows.operations.device_lifecycle.discover_network_device", "discover_network_device")
LazyWorkflowInstance("workflows.operations.device_lifecycle.onboard_network_device", "onboard_network_device")
LazyWorkflowInstance("workflows.operations.device_lifecycle.device_health_check", "device_health_check")
LazyWorkflowInstance("workflows.operations.device_lifecycle.bootstrap_device_configuration", "bootstrap_device_configuration")
LazyWorkflowInstance("workflows.operations.device_lifecycle.deploy_configuration_template", "deploy_configuration_template")

LazyWorkflowInstance("workflows.operations.vlan_management.vlan_management", "create_vlan")
LazyWorkflowInstance("workflows.operations.vlan_management.vlan_management", "modify_vlan")
LazyWorkflowInstance("workflows.operations.vlan_management.delete_vlan", "delete_vlan")

LazyWorkflowInstance("workflows.operations.port_management.configure_port_channel", "configure_port_channel")

LazyWorkflowInstance("workflows.operations.routing_switching.configure_ospf", "configure_ospf")
LazyWorkflowInstance("workflows.operations.routing_switching.configure_bgp", "configure_bgp_protocol")

LazyWorkflowInstance("workflows.operations.qos_management.configure_qos_policy", "configure_qos_policy")

LazyWorkflowInstance("workflows.operations.monitoring.setup_network_monitoring", "setup_network_monitoring")

# Network Automation Workflows - Intent-Based Group
LazyWorkflowInstance("workflows.intent_based.service_orchestration.l3vpn_service", "deploy_l3vpn_service")
LazyWorkflowInstance("workflows.intent_based.wireless_management.mist_wireless_service", "deploy_wireless_service")

"""
Master Workflow Registry
Central registration and discovery system for all network automation workflows
"""

import importlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import workflow group registrations
try:
    from workflows.operations import (
        register_operations_workflows, 
        OPERATIONS_WORKFLOW_CATEGORIES,
        OPERATIONS_CAPABILITIES
    )
    operations_available = True
except ImportError:
    print("⚠️  Operations workflows not available")
    operations_available = False

try:
    from workflows.intent_based import (
        register_intent_based_workflows,
        INTENT_BASED_WORKFLOW_CATEGORIES, 
        INTENT_BASED_CAPABILITIES
    )
    intent_based_available = True
except ImportError:
    print("⚠️  Intent-based workflows not available")
    intent_based_available = False


class WorkflowGroup(Enum):
    OPERATIONS = "operations"
    INTENT_BASED = "intent_based"
    HYBRID = "hybrid"


@dataclass
class WorkflowRegistration:
    """Workflow registration metadata"""
    workflow_function: callable
    name: str
    description: str
    category: str
    group: WorkflowGroup
    tags: List[str] = field(default_factory=list)
    complexity: str = "medium"
    estimated_duration: str = "5-15 minutes"
    automation_level: str = "manual"
    rollback_supported: bool = False
    ai_enabled: bool = False
    multi_vendor: bool = True
    prerequisites: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


class WorkflowRegistry:
    """Central workflow registry for discovery and management"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowRegistration] = {}
        self.categories: Dict[str, List[str]] = {}
        self.groups: Dict[WorkflowGroup, List[str]] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the workflow registry with all available workflows"""
        print("🚀 Initializing Network Automation Workflow Registry...")
        
        # Register operations workflows
        if operations_available:
            try:
                operations_workflows = register_operations_workflows()
                for workflow_config in operations_workflows:
                    self._register_workflow(workflow_config, WorkflowGroup.OPERATIONS)
                print(f"✅ Registered {len(operations_workflows)} operations workflows")
            except Exception as e:
                print(f"❌ Failed to register operations workflows: {str(e)}")
        
        # Register intent-based workflows  
        if intent_based_available:
            try:
                intent_based_workflows = register_intent_based_workflows()
                for workflow_config in intent_based_workflows:
                    self._register_workflow(workflow_config, WorkflowGroup.INTENT_BASED)
                print(f"✅ Registered {len(intent_based_workflows)} intent-based workflows")
            except Exception as e:
                print(f"❌ Failed to register intent-based workflows: {str(e)}")
        
        self._organize_by_categories()
        self._organize_by_groups()
        
        print(f"\n📊 Workflow Registry Summary:")
        print(f"Total workflows: {len(self.workflows)}")
        print(f"Categories: {len(self.categories)}")
        print(f"Groups: {len(self.groups)}")
    
    def _register_workflow(self, workflow_config: dict, group: WorkflowGroup):
        """Register a single workflow"""
        try:
            metadata = workflow_config["metadata"]
            workflow_id = self._generate_workflow_id(metadata["name"])
            
            registration = WorkflowRegistration(
                workflow_function=workflow_config["workflow_function"],
                name=metadata["name"],
                description=metadata["description"],
                category=metadata["category"],
                group=group,
                tags=metadata.get("tags", []),
                complexity=metadata.get("complexity", "medium"),
                estimated_duration=metadata.get("estimated_duration", "5-15 minutes"),
                automation_level=metadata.get("automation_level", "manual"),
                rollback_supported=metadata.get("rollback_supported", False),
                ai_enabled=metadata.get("ai_enabled", False),
                multi_vendor=metadata.get("multi_vendor", True),
                prerequisites=metadata.get("prerequisites", []),
                outputs=metadata.get("outputs", [])
            )
            
            self.workflows[workflow_id] = registration
            
        except Exception as e:
            print(f"❌ Failed to register workflow {workflow_config.get('name', 'unknown')}: {str(e)}")
    
    def _generate_workflow_id(self, name: str) -> str:
        """Generate a unique workflow ID from name"""
        return name.lower().replace(" ", "_").replace("-", "_")
    
    def _organize_by_categories(self):
        """Organize workflows by category"""
        for workflow_id, registration in self.workflows.items():
            category = registration.category
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(workflow_id)
    
    def _organize_by_groups(self):
        """Organize workflows by group"""
        for workflow_id, registration in self.workflows.items():
            group = registration.group
            if group not in self.groups:
                self.groups[group] = []
            self.groups[group].append(workflow_id)
    
    # Query methods
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowRegistration]:
        """Get a specific workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def get_workflows_by_category(self, category: str) -> List[WorkflowRegistration]:
        """Get all workflows in a category"""
        workflow_ids = self.categories.get(category, [])
        return [self.workflows[wid] for wid in workflow_ids]
    
    def get_workflows_by_group(self, group: WorkflowGroup) -> List[WorkflowRegistration]:
        """Get all workflows in a group"""
        workflow_ids = self.groups.get(group, [])
        return [self.workflows[wid] for wid in workflow_ids]
    
    def get_workflows_by_tags(self, tags: List[str]) -> List[WorkflowRegistration]:
        """Get workflows containing any of the specified tags"""
        matching_workflows = []
        for registration in self.workflows.values():
            if any(tag in registration.tags for tag in tags):
                matching_workflows.append(registration)
        return matching_workflows
    
    def get_ai_enabled_workflows(self) -> List[WorkflowRegistration]:
        """Get all AI-enabled workflows"""
        return [reg for reg in self.workflows.values() if reg.ai_enabled]
    
    def get_workflows_by_complexity(self, complexity: str) -> List[WorkflowRegistration]:
        """Get workflows by complexity level"""
        return [reg for reg in self.workflows.values() if reg.complexity == complexity]
    
    def search_workflows(self, query: str) -> List[WorkflowRegistration]:
        """Search workflows by name, description, or tags"""
        query_lower = query.lower()
        matching_workflows = []
        
        for registration in self.workflows.values():
            # Search in name, description, and tags
            if (query_lower in registration.name.lower() or 
                query_lower in registration.description.lower() or
                any(query_lower in tag.lower() for tag in registration.tags)):
                matching_workflows.append(registration)
        
        return matching_workflows
    
    # Dashboard methods
    def get_workflow_dashboard_data(self) -> dict:
        """Get data for workflow dashboard"""
        return {
            "summary": {
                "total_workflows": len(self.workflows),
                "operations_workflows": len(self.get_workflows_by_group(WorkflowGroup.OPERATIONS)),
                "intent_based_workflows": len(self.get_workflows_by_group(WorkflowGroup.INTENT_BASED)),
                "ai_enabled_workflows": len(self.get_ai_enabled_workflows()),
                "categories": len(self.categories)
            },
            "categories": self._get_category_data(),
            "groups": self._get_group_data(),
            "complexity_distribution": self._get_complexity_distribution(),
            "automation_levels": self._get_automation_levels(),
            "recent_workflows": list(self.workflows.values())[-5:] if self.workflows else []
        }
    
    def _get_category_data(self) -> dict:
        """Get category data for dashboard"""
        category_data = {}
        
        # Add operations categories
        if operations_available:
            for cat in OPERATIONS_WORKFLOW_CATEGORIES:
                category_data[cat["name"]] = {
                    "description": cat["description"],
                    "icon": cat["icon"],
                    "color": cat["color"],
                    "workflow_count": len(self.get_workflows_by_category(cat["name"])),
                    "features": cat["features"],
                    "group": "operations"
                }
        
        # Add intent-based categories  
        if intent_based_available:
            for cat in INTENT_BASED_WORKFLOW_CATEGORIES:
                category_data[cat["name"]] = {
                    "description": cat["description"],
                    "icon": cat["icon"],
                    "color": cat["color"],
                    "workflow_count": len(self.get_workflows_by_category(cat["name"])),
                    "features": cat["features"],
                    "ai_enabled": cat.get("ai_enabled", False),
                    "group": "intent_based"
                }
        
        return category_data
    
    def _get_group_data(self) -> dict:
        """Get group data for dashboard"""
        return {
            "operations": {
                "name": "Operations Workflows",
                "description": "Traditional network operations and maintenance workflows",
                "count": len(self.get_workflows_by_group(WorkflowGroup.OPERATIONS)),
                "capabilities": OPERATIONS_CAPABILITIES if operations_available else {}
            },
            "intent_based": {
                "name": "Intent-Based Workflows", 
                "description": "AI-driven intent-based network automation workflows",
                "count": len(self.get_workflows_by_group(WorkflowGroup.INTENT_BASED)),
                "capabilities": INTENT_BASED_CAPABILITIES if intent_based_available else {}
            }
        }
    
    def _get_complexity_distribution(self) -> dict:
        """Get workflow complexity distribution"""
        complexity_count = {}
        for registration in self.workflows.values():
            complexity = registration.complexity
            complexity_count[complexity] = complexity_count.get(complexity, 0) + 1
        return complexity_count
    
    def _get_automation_levels(self) -> dict:
        """Get automation level distribution"""
        automation_count = {}
        for registration in self.workflows.values():
            level = registration.automation_level
            automation_count[level] = automation_count.get(level, 0) + 1
        return automation_count


# Global workflow registry instance
workflow_registry = WorkflowRegistry()


# Convenience functions for easy access
def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry instance"""
    return workflow_registry


def get_all_workflows() -> Dict[str, WorkflowRegistration]:
    """Get all registered workflows"""
    return workflow_registry.workflows


def find_workflows(query: str = None, category: str = None, 
                  group: WorkflowGroup = None, tags: List[str] = None) -> List[WorkflowRegistration]:
    """Find workflows with flexible search criteria"""
    if query:
        return workflow_registry.search_workflows(query)
    elif category:
        return workflow_registry.get_workflows_by_category(category)
    elif group:
        return workflow_registry.get_workflows_by_group(group)
    elif tags:
        return workflow_registry.get_workflows_by_tags(tags)
    else:
        return list(workflow_registry.workflows.values())


def get_dashboard_data() -> dict:
    """Get workflow dashboard data"""
    return workflow_registry.get_workflow_dashboard_data()


# Initialize registry on import
print("🌐 Network Automation Workflow Registry Initialized")
