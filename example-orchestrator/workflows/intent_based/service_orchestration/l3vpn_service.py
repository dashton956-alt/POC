"""
L3VPN Service Orchestration Workflow
Intent-based end-to-end L3VPN service provisioning
"""

from orchestrator import workflow
from orchestrator.forms import FormPage
from orchestrator.targets import Target
from orchestrator.types import State, SubscriptionLifecycle, UUIDstr
from orchestrator.workflow import Step, StepList, begin, done
from orchestrator.workflows.steps import store_process_subscription
from pydantic import Field, validator
from pydantic_forms.core import FormPage
from pydantic_forms.types import Choice
from typing import List, Dict, Any, Optional

from products.product_types.l3vpn import L3VpnInactive, L3VpnProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from workflows.shared import device_selector, bandwidth_selector


class L3VpnServiceForm(FormPage):
    """L3VPN Service Intent Form"""
    
    # Service Identity
    service_name: str = Field(
        description="Service Name",
        min_length=3,
        max_length=64
    )
    service_description: str = Field(
        description="Service Description",
        default=""
    )
    customer_id: str = Field(
        description="Customer Identifier"
    )
    
    # Service Intent
    service_type: Choice = Field(
        description="L3VPN Service Type",
        choices=[
            ("any_to_any", "Any-to-Any (Full Mesh)"),
            ("hub_and_spoke", "Hub and Spoke"),
            ("hub_spoke_with_spoke_to_spoke", "Hub-Spoke with Spoke-to-Spoke"),
            ("extranet", "Extranet VPN"),
            ("internet_access", "Internet Access VPN")
        ],
        default="any_to_any"
    )
    
    # Quality of Service Intent
    qos_class: Choice = Field(
        description="Quality of Service Class",
        choices=[
            ("best_effort", "Best Effort"),
            ("bronze", "Bronze (Low Priority)"),
            ("silver", "Silver (Medium Priority)"),
            ("gold", "Gold (High Priority)"),
            ("platinum", "Platinum (Real-time)")
        ],
        default="silver"
    )
    
    # Bandwidth Requirements
    bandwidth_requirements: Choice = Field(
        description="Bandwidth Requirements",
        choices=[
            ("low", "Low (< 10 Mbps)"),
            ("medium", "Medium (10-100 Mbps)"),
            ("high", "High (100 Mbps - 1 Gbps)"),
            ("very_high", "Very High (> 1 Gbps)")
        ],
        default="medium"
    )
    
    # Security Intent
    security_level: Choice = Field(
        description="Security Level",
        choices=[
            ("basic", "Basic Security"),
            ("standard", "Standard Security"),
            ("high", "High Security"),
            ("government", "Government Grade")
        ],
        default="standard"
    )
    
    # Site Endpoints
    hub_sites: List[Dict[str, Any]] = Field(
        description="Hub Site Definitions",
        default=[]
    )
    spoke_sites: List[Dict[str, Any]] = Field(
        description="Spoke Site Definitions", 
        default=[]
    )
    
    # Service Level Agreements
    availability_sla: float = Field(
        description="Availability SLA (%)",
        ge=95.0,
        le=100.0,
        default=99.9
    )
    
    latency_sla: int = Field(
        description="Maximum Latency (ms)",
        ge=1,
        le=1000,
        default=50
    )
    
    # Advanced Options
    enable_multicast: bool = Field(
        description="Enable Multicast Support",
        default=False
    )
    
    enable_ipv6: bool = Field(
        description="Enable IPv6 Support", 
        default=True
    )
    
    route_distinguisher_pool: str = Field(
        description="Route Distinguisher Pool",
        default="auto"
    )
    
    rt_import_export_policy: Choice = Field(
        description="RT Import/Export Policy",
        choices=[
            ("auto", "Automatic"),
            ("custom", "Custom Policy"),
            ("central_hub", "Central Hub Policy")
        ],
        default="auto"
    )


class SiteEndpointForm(FormPage):
    """Site Endpoint Configuration"""
    site_name: str = Field(description="Site Name")
    site_location: str = Field(description="Site Location/Address")
    device_id: str = Field(description="PE Router Device ID")
    interface_id: str = Field(description="Customer Facing Interface")
    vlan_id: Optional[int] = Field(description="Customer VLAN ID", ge=1, le=4094)
    ip_network: str = Field(description="Customer IP Network (CIDR)")
    bandwidth_mbps: int = Field(description="Bandwidth (Mbps)", ge=1, le=10000)
    site_role: Choice = Field(
        description="Site Role",
        choices=[
            ("hub", "Hub Site"),
            ("spoke", "Spoke Site"),
            ("backup_hub", "Backup Hub")
        ]
    )


@workflow("Deploy L3VPN Service", target=Target.CREATE)
def deploy_l3vpn_service() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> analyze_service_intent
        >> discover_network_resources
        >> design_vpn_topology  
        >> allocate_network_resources
        >> generate_device_configurations
        >> deploy_configurations
        >> configure_routing_policies
        >> establish_vpn_tunnels
        >> configure_qos_policies
        >> validate_service_connectivity
        >> register_service_monitoring
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate L3VPN service intent form"""
    return L3VpnServiceForm


def analyze_service_intent(subscription: L3VpnInactive) -> L3VpnProvisioning:
    """Analyze service intent and translate to technical requirements"""
    subscription = L3VpnProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    # Translate business intent to technical requirements
    technical_requirements = {
        "topology_type": subscription.service_type,
        "qos_marking": map_qos_class_to_dscp(subscription.qos_class),
        "bandwidth_profile": calculate_bandwidth_profile(subscription.bandwidth_requirements),
        "security_controls": derive_security_controls(subscription.security_level),
        "routing_protocol": "BGP",  # L3VPN uses BGP
        "vpn_technology": "MPLS_L3VPN",
        "redundancy_requirements": derive_redundancy_from_sla(subscription.availability_sla)
    }
    
    subscription.technical_requirements = technical_requirements
    subscription.total_sites = len(subscription.hub_sites) + len(subscription.spoke_sites)
    
    return subscription


def discover_network_resources(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Discover available network resources for service"""
    
    # Discovery callback
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/discovery"
    
    # Collect all site devices
    site_devices = []
    all_sites = subscription.hub_sites + subscription.spoke_sites
    
    for site in all_sites:
        site_devices.append(site["device_id"])
    
    # Get device details from NetBox
    discovered_resources = {
        "pe_routers": [],
        "available_interfaces": {},
        "ip_address_pools": [],
        "vrf_availability": {},
        "mpls_label_pools": []
    }
    
    for device_id in site_devices:
        device = netbox.get_device(device_id)
        interfaces = netbox.get_device_interfaces(device_id, available_only=True)
        
        discovered_resources["pe_routers"].append({
            "device_id": device_id,
            "device_name": device["name"],
            "management_ip": device.get("primary_ip4"),
            "platform": device.get("platform"),
            "site": device.get("site")
        })
        
        discovered_resources["available_interfaces"][device_id] = interfaces
    
    # Query IP address pools
    available_prefixes = netbox.get_available_prefixes(
        family=4,  # IPv4
        mask_length_gte=24,
        mask_length_lte=30
    )
    
    discovered_resources["ip_address_pools"] = available_prefixes[:10]  # Limit results
    
    subscription.discovered_resources = discovered_resources
    
    return subscription


def design_vpn_topology(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Design VPN topology based on service intent"""
    
    topology_design = {
        "service_name": subscription.service_name,
        "topology_type": subscription.service_type,
        "vrf_name": f"VRF_{subscription.customer_id}_{subscription.service_name}",
        "route_distinguisher": generate_route_distinguisher(subscription),
        "route_targets": generate_route_targets(subscription),
        "sites": [],
        "routing_policies": [],
        "qos_policies": []
    }
    
    # Design hub-spoke or full-mesh topology
    if subscription.service_type == "hub_and_spoke":
        topology_design = design_hub_spoke_topology(subscription, topology_design)
    elif subscription.service_type == "any_to_any":
        topology_design = design_full_mesh_topology(subscription, topology_design)
    
    # Add QoS design
    topology_design["qos_policies"] = design_qos_policies(subscription)
    
    subscription.topology_design = topology_design
    
    return subscription


def allocate_network_resources(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Allocate specific network resources for the service"""
    
    resource_allocation = {
        "vrf_id": generate_vrf_id(),
        "route_distinguisher": subscription.topology_design["route_distinguisher"],
        "route_targets": subscription.topology_design["route_targets"],
        "allocated_prefixes": {},
        "allocated_interfaces": {},
        "mpls_labels": {}
    }
    
    # Allocate IP prefixes for each site
    all_sites = subscription.hub_sites + subscription.spoke_sites
    prefix_pool = iter(subscription.discovered_resources["ip_address_pools"])
    
    for site in all_sites:
        site_prefix = next(prefix_pool)
        resource_allocation["allocated_prefixes"][site["site_name"]] = {
            "customer_network": site["ip_network"],
            "pe_ce_link": site_prefix,
            "loopback": generate_loopback_ip()
        }
    
    # Reserve NetBox resources
    for site_name, allocation in resource_allocation["allocated_prefixes"].items():
        netbox.create_prefix({
            "prefix": allocation["pe_ce_link"],
            "description": f"L3VPN {subscription.service_name} - {site_name} PE-CE link",
            "vrf": resource_allocation["vrf_id"],
            "status": "reserved"
        })
    
    subscription.resource_allocation = resource_allocation
    
    return subscription


def generate_device_configurations(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Generate device-specific configurations"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/config_gen"
    
    # Prepare configuration generation data
    config_data = {
        "service": {
            "name": subscription.service_name,
            "customer_id": subscription.customer_id,
            "vrf_name": subscription.topology_design["vrf_name"],
            "route_distinguisher": subscription.resource_allocation["route_distinguisher"],
            "route_targets": subscription.resource_allocation["route_targets"]
        },
        "sites": subscription.hub_sites + subscription.spoke_sites,
        "topology": subscription.topology_design,
        "resources": subscription.resource_allocation,
        "qos_requirements": subscription.technical_requirements
    }
    
    # Get PE router inventory
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    execute_playbook(
        playbook_name="generate_l3vpn_configurations.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=config_data
    )
    
    return subscription


def deploy_configurations(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Deploy generated configurations to PE routers"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/deploy_config"
    
    # Get PE router inventory
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    deployment_data = {
        "service_name": subscription.service_name,
        "vrf_name": subscription.topology_design["vrf_name"],
        "deployment_mode": "staged",  # Deploy in stages for safety
        "rollback_enabled": True,
        "generated_configs": subscription.generated_configs  # From previous step
    }
    
    execute_playbook(
        playbook_name="deploy_l3vpn_configurations.yaml", 
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=deployment_data
    )
    
    return subscription


def configure_routing_policies(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Configure BGP routing policies for the L3VPN"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/routing"
    
    routing_data = {
        "vrf_name": subscription.topology_design["vrf_name"], 
        "service_type": subscription.service_type,
        "route_policies": subscription.topology_design["routing_policies"],
        "hub_sites": subscription.hub_sites,
        "spoke_sites": subscription.spoke_sites
    }
    
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    execute_playbook(
        playbook_name="configure_l3vpn_routing.yaml",
        callback_route=callback_route, 
        inventory=inventory,
        extra_vars=routing_data
    )
    
    return subscription


def establish_vpn_tunnels(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Establish MPLS L3VPN tunnels between sites"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/tunnels"
    
    tunnel_data = {
        "vrf_name": subscription.topology_design["vrf_name"],
        "tunnel_type": "MPLS_LSP",
        "topology_design": subscription.topology_design,
        "redundancy_required": subscription.technical_requirements["redundancy_requirements"]
    }
    
    # Focus on PE routers for tunnel establishment
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    execute_playbook(
        playbook_name="establish_l3vpn_tunnels.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=tunnel_data
    )
    
    return subscription


def configure_qos_policies(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Configure Quality of Service policies"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/qos"
    
    qos_data = {
        "qos_class": subscription.qos_class,
        "bandwidth_profile": subscription.technical_requirements["bandwidth_profile"],
        "latency_sla": subscription.latency_sla,
        "qos_policies": subscription.topology_design["qos_policies"]
    }
    
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    execute_playbook(
        playbook_name="configure_l3vpn_qos.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=qos_data
    )
    
    return subscription


def validate_service_connectivity(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Validate end-to-end service connectivity"""
    
    callback_route = f"/api/workflows/l3vpn/deploy/{subscription.subscription_id}/validate"
    
    validation_data = {
        "service_name": subscription.service_name,
        "vrf_name": subscription.topology_design["vrf_name"],
        "expected_sites": len(subscription.hub_sites) + len(subscription.spoke_sites),
        "connectivity_tests": generate_connectivity_tests(subscription),
        "sla_requirements": {
            "availability": subscription.availability_sla,
            "latency": subscription.latency_sla
        }
    }
    
    pe_devices = [r["management_ip"] for r in subscription.discovered_resources["pe_routers"]]
    inventory = "\n".join(pe_devices) + "\n"
    
    execute_playbook(
        playbook_name="validate_l3vpn_service.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=validation_data
    )
    
    return subscription


def register_service_monitoring(subscription: L3VpnProvisioning) -> L3VpnProvisioning:
    """Register service for monitoring and SLA tracking"""
    
    monitoring_config = {
        "service_id": subscription.subscription_id,
        "service_name": subscription.service_name,
        "customer_id": subscription.customer_id,
        "monitoring_points": [],
        "sla_thresholds": {
            "availability": subscription.availability_sla,
            "latency": subscription.latency_sla,
            "packet_loss": 0.1  # Default 0.1%
        },
        "alerting_enabled": True
    }
    
    # Create monitoring points for each site
    all_sites = subscription.hub_sites + subscription.spoke_sites
    for site in all_sites:
        monitoring_config["monitoring_points"].append({
            "site_name": site["site_name"],
            "device_ip": get_device_ip(site["device_id"]),
            "interface": site["interface_id"],
            "metrics": ["availability", "latency", "bandwidth", "packet_loss"]
        })
    
    # Register with monitoring system (placeholder)
    subscription.monitoring_registered = True
    subscription.monitoring_config = monitoring_config
    
    return subscription


# Helper functions
def map_qos_class_to_dscp(qos_class: str) -> str:
    """Map QoS class to DSCP marking"""
    qos_mapping = {
        "best_effort": "0",
        "bronze": "10", 
        "silver": "18",
        "gold": "26",
        "platinum": "46"
    }
    return qos_mapping.get(qos_class, "0")


def calculate_bandwidth_profile(bandwidth_req: str) -> Dict[str, int]:
    """Calculate bandwidth profile from requirements"""
    profiles = {
        "low": {"cir": 5, "pir": 10, "cbs": 1000, "pbs": 2000},
        "medium": {"cir": 50, "pir": 100, "cbs": 10000, "pbs": 20000},
        "high": {"cir": 500, "pir": 1000, "cbs": 100000, "pbs": 200000},
        "very_high": {"cir": 1000, "pir": 2000, "cbs": 200000, "pbs": 400000}
    }
    return profiles.get(bandwidth_req, profiles["medium"])


def derive_security_controls(security_level: str) -> List[str]:
    """Derive security controls from security level"""
    controls = {
        "basic": ["acl_filtering"],
        "standard": ["acl_filtering", "encryption"],
        "high": ["acl_filtering", "encryption", "authentication", "integrity_check"],
        "government": ["acl_filtering", "encryption", "authentication", "integrity_check", "key_rotation"]
    }
    return controls.get(security_level, controls["standard"])


def derive_redundancy_from_sla(availability_sla: float) -> str:
    """Derive redundancy requirements from availability SLA"""
    if availability_sla >= 99.99:
        return "dual_homed"
    elif availability_sla >= 99.9:
        return "backup_path" 
    else:
        return "single_path"


def generate_route_distinguisher(subscription) -> str:
    """Generate unique route distinguisher"""
    return f"65000:{subscription.subscription_id[:8]}"


def generate_route_targets(subscription) -> Dict[str, str]:
    """Generate import/export route targets"""
    base_rt = f"65000:{subscription.subscription_id[:8]}"
    return {
        "import": base_rt,
        "export": base_rt
    }


def generate_connectivity_tests(subscription) -> List[Dict]:
    """Generate connectivity tests for validation"""
    tests = []
    all_sites = subscription.hub_sites + subscription.spoke_sites
    
    # Create mesh connectivity tests
    for i, site1 in enumerate(all_sites):
        for site2 in all_sites[i+1:]:
            tests.append({
                "source_site": site1["site_name"],
                "destination_site": site2["site_name"], 
                "test_type": "ping",
                "expected_result": "success"
            })
    
    return tests
