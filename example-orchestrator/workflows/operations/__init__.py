"""
Operations Workflow Group Registration
Register all operations-focused network workflows
"""

from workflows.operations.device_lifecycle.discover_network_device import discover_network_device
from workflows.operations.device_lifecycle.onboard_network_device import onboard_network_device  
from workflows.operations.device_lifecycle.device_health_check import device_health_check
from workflows.operations.device_lifecycle.bootstrap_device_configuration import bootstrap_device_configuration
from workflows.operations.device_lifecycle.deploy_configuration_template import deploy_configuration_template

from workflows.operations.vlan_management.vlan_management import create_vlan, modify_vlan
from workflows.operations.vlan_management.delete_vlan import delete_vlan

from workflows.operations.port_management.configure_port_channel import configure_port_channel

from workflows.operations.routing_switching.configure_ospf import configure_ospf
from workflows.operations.routing_switching.configure_bgp import configure_bgp_protocol

from workflows.operations.qos_management.configure_qos_policy import configure_qos_policy

from workflows.operations.monitoring.setup_network_monitoring import setup_network_monitoring

# Device Lifecycle Management Workflows
DEVICE_LIFECYCLE_WORKFLOWS = [
    {
        "workflow": discover_network_device,
        "name": "Discover Network Device",
        "description": "Auto-discover devices via SNMP, LLDP, CDP and create inventory records",
        "category": "Device Lifecycle",
        "tags": ["discovery", "inventory", "snmp", "lldp"],
        "complexity": "medium",
        "estimated_duration": "5-15 minutes"
    },
    {
        "workflow": onboard_network_device,
        "name": "Onboard Network Device", 
        "description": "Complete device provisioning with initial configuration and monitoring setup",
        "category": "Device Lifecycle",
        "tags": ["onboarding", "provisioning", "configuration"],
        "complexity": "high",
        "estimated_duration": "20-45 minutes"
    },
    {
        "workflow": device_health_check,
        "name": "Device Health Check",
        "description": "Comprehensive device validation including hardware, software, and services",
        "category": "Device Lifecycle", 
        "tags": ["health", "monitoring", "validation", "diagnostics"],
        "complexity": "medium",
        "estimated_duration": "10-20 minutes"
    },
    {
        "workflow": bootstrap_device_configuration,
        "name": "Bootstrap Device Configuration",
        "description": "Apply initial day-0 configuration to network devices",
        "category": "Device Lifecycle",
        "tags": ["bootstrap", "day0", "initial_config", "ztp"],
        "complexity": "high", 
        "estimated_duration": "15-30 minutes"
    },
    {
        "workflow": deploy_configuration_template,
        "name": "Deploy Configuration Template",
        "description": "Apply standardized device configurations using templates",
        "category": "Device Lifecycle",
        "tags": ["template", "standardization", "configuration", "deployment"],
        "complexity": "high",
        "estimated_duration": "20-60 minutes"
    }
]

# VLAN Management Workflows  
VLAN_MANAGEMENT_WORKFLOWS = [
    {
        "workflow": create_vlan,
        "name": "Create VLAN",
        "description": "Provision Layer 2 broadcast domains across network infrastructure",
        "category": "VLAN Management",
        "tags": ["vlan", "layer2", "provisioning"],
        "complexity": "medium", 
        "estimated_duration": "5-15 minutes"
    },
    {
        "workflow": modify_vlan,
        "name": "Modify VLAN Configuration",
        "description": "Update VLAN parameters and assignments with impact analysis",
        "category": "VLAN Management",
        "tags": ["vlan", "modification", "change_management"],
        "complexity": "medium",
        "estimated_duration": "10-20 minutes"
    },
    {
        "workflow": delete_vlan,
        "name": "Delete VLAN",
        "description": "Remove unused VLAN and cleanup associated resources safely",
        "category": "VLAN Management", 
        "tags": ["vlan", "deletion", "cleanup", "resource_management"],
        "complexity": "high",
        "estimated_duration": "15-45 minutes"
    }
]

# Port & Interface Management Workflows
PORT_INTERFACE_WORKFLOWS = [
    {
        "workflow": configure_port_channel,
        "name": "Configure Port Channel/LAG",
        "description": "Create link aggregation groups for high availability and load balancing",
        "category": "Interface Management",
        "tags": ["portchannel", "lag", "lacp", "high_availability"],
        "complexity": "high",
        "estimated_duration": "20-40 minutes"
    }
]

# Routing & Switching Workflows
ROUTING_SWITCHING_WORKFLOWS = [
    {
        "workflow": configure_ospf,
        "name": "Configure OSPF",
        "description": "Deploy OSPF routing protocol with area design and optimization",
        "category": "Routing & Switching",
        "tags": ["ospf", "routing", "igp", "area_design"],
        "complexity": "very_high",
        "estimated_duration": "30-90 minutes"
    }
]# VLAN Management Workflows  
VLAN_MANAGEMENT_WORKFLOWS = [
    {
        "workflow": create_vlan,
        "name": "Create VLAN",
        "description": "Provision Layer 2 broadcast domains across network infrastructure",
        "category": "VLAN Management",
        "tags": ["vlan", "layer2", "switching", "broadcast_domain"],
        "complexity": "medium",
        "estimated_duration": "3-8 minutes"
    },
    {
        "workflow": modify_vlan,
        "name": "Modify VLAN",
        "description": "Update VLAN parameters and device assignments",
        "category": "VLAN Management", 
        "tags": ["vlan", "modification", "network_change"],
        "complexity": "medium",
        "estimated_duration": "2-5 minutes"
    },
    {
        "workflow": delete_vlan,
        "name": "Delete VLAN",
        "description": "Safely remove VLANs with comprehensive dependency analysis",
        "category": "VLAN Management",
        "tags": ["vlan", "deletion", "cleanup", "dependency_analysis"],
        "complexity": "high",
        "estimated_duration": "5-15 minutes"
    }
]

# Interface Management Workflows
INTERFACE_MANAGEMENT_WORKFLOWS = [
    {
        "workflow": configure_port_channel,
        "name": "Configure Port Channel",
        "description": "Create and manage link aggregation groups for high availability",
        "category": "Interface Management",
        "tags": ["port_channel", "lag", "link_aggregation", "high_availability"],
        "complexity": "high",
        "estimated_duration": "10-20 minutes"
    }
]

# Routing & Switching Workflows
ROUTING_SWITCHING_WORKFLOWS = [
    {
        "workflow": configure_ospf,
        "name": "Configure OSPF",
        "description": "Deploy OSPF routing protocol with area design and authentication",
        "category": "Routing & Switching",
        "tags": ["ospf", "routing", "igp", "area_design"],
        "complexity": "very_high",
        "estimated_duration": "20-45 minutes"
    },
    {
        "workflow": configure_bgp_protocol,
        "name": "Configure BGP",
        "description": "Deploy BGP routing protocol with neighbor relationships and route policies",
        "category": "Routing & Switching",
        "tags": ["bgp", "routing", "egp", "external_peering"],
        "complexity": "very_high",
        "estimated_duration": "25-60 minutes"
    }
]

# Monitoring Workflows
MONITORING_WORKFLOWS = [
    {
        "workflow": setup_network_monitoring,
        "name": "Setup Network Monitoring",
        "description": "Configure comprehensive network monitoring with SNMP, flow analysis, and health checks",
        "category": "Monitoring",
        "tags": ["monitoring", "snmp", "netflow", "health_checks", "observability"],
        "complexity": "high",
        "estimated_duration": "15-30 minutes"
    }
]

# QoS Management Workflows  
QOS_MANAGEMENT_WORKFLOWS = [
    {
        "workflow": configure_qos_policy,
        "name": "Configure QoS Policy",
        "description": "Deploy Quality of Service policies for traffic prioritization and bandwidth management",
        "category": "QoS Management",
        "tags": ["qos", "traffic_shaping", "bandwidth", "prioritization", "classification"],
        "complexity": "very_high",
        "estimated_duration": "20-45 minutes"
    }
]

# Combine all operations workflows
ALL_OPERATIONS_WORKFLOWS = (
    DEVICE_LIFECYCLE_WORKFLOWS +
    VLAN_MANAGEMENT_WORKFLOWS + 
    INTERFACE_MANAGEMENT_WORKFLOWS +
    ROUTING_SWITCHING_WORKFLOWS +
    QOS_MANAGEMENT_WORKFLOWS +
    MONITORING_WORKFLOWS
)


def register_operations_workflows():
    """Register all operations workflows with the orchestrator"""
    registered_workflows = []
    
    for workflow_config in ALL_OPERATIONS_WORKFLOWS:
        try:
            # Register workflow with orchestrator
            workflow_registration = {
                "workflow_function": workflow_config["workflow"],
                "metadata": {
                    "name": workflow_config["name"],
                    "description": workflow_config["description"],
                    "category": workflow_config["category"],
                    "group": "Operations",
                    "tags": workflow_config["tags"],
                    "complexity": workflow_config["complexity"],
                    "estimated_duration": workflow_config["estimated_duration"],
                    "workflow_type": "operations"
                }
            }
            
            registered_workflows.append(workflow_registration)
            print(f"✅ Registered operations workflow: {workflow_config['name']}")
            
        except Exception as e:
            print(f"❌ Failed to register workflow {workflow_config['name']}: {str(e)}")
    
    print(f"\n📊 Operations Workflow Registration Summary:")
    print(f"Total workflows registered: {len(registered_workflows)}")
    print(f"Device Lifecycle: {len(DEVICE_LIFECYCLE_WORKFLOWS)}")
    print(f"VLAN Management: {len(VLAN_MANAGEMENT_WORKFLOWS)}")
    print(f"Interface Management: {len(INTERFACE_MANAGEMENT_WORKFLOWS)}")
    print(f"Routing & Switching: {len(ROUTING_SWITCHING_WORKFLOWS)}")
    print(f"Monitoring: {len(MONITORING_WORKFLOWS)}")
    
    return registered_workflows


# Workflow categories for UI organization
OPERATIONS_WORKFLOW_CATEGORIES = [
    {
        "name": "Device Lifecycle", 
        "description": "Device discovery, onboarding, and lifecycle management",
        "icon": "device-desktop",
        "workflows": [w["name"] for w in DEVICE_LIFECYCLE_WORKFLOWS]
    },
    {
        "name": "VLAN Management",
        "description": "VLAN creation, modification, and management", 
        "icon": "network-wired",
        "workflows": [w["name"] for w in VLAN_MANAGEMENT_WORKFLOWS]
    },
    {
        "name": "Interface Management", 
        "description": "Port and interface configuration management",
        "icon": "plug",
        "workflows": [w["name"] for w in INTERFACE_MANAGEMENT_WORKFLOWS]
    },
    {
        "name": "Routing & Switching",
        "description": "Layer 3 routing and switching protocols",
        "icon": "route", 
        "workflows": [w["name"] for w in ROUTING_SWITCHING_WORKFLOWS]
    },
    {
        "name": "QoS Management",
        "description": "Quality of Service and traffic management",
        "icon": "tachometer-alt",
        "workflows": [w["name"] for w in QOS_MANAGEMENT_WORKFLOWS]
    },
    {
        "name": "Monitoring",
        "description": "Network monitoring and observability",
        "icon": "chart-line",
        "workflows": [w["name"] for w in MONITORING_WORKFLOWS]  
    }
]
