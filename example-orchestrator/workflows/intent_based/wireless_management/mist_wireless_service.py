"""
Mist Cloud Wireless Management Workflow
Intent-based wireless network provisioning and management
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

from products.product_types.wireless import WirelessInactive, WirelessProvisioning
from services.mist_api import mist_client
from services.netbox import netbox
from services.lso_client import execute_playbook
from workflows.shared import site_selector


class WirelessNetworkIntentForm(FormPage):
    """Wireless Network Service Intent"""
    
    # Service Identity
    network_name: str = Field(
        description="Wireless Network Name (SSID)",
        min_length=1,
        max_length=32
    )
    
    service_description: str = Field(
        description="Service Description",
        default=""
    )
    
    # Coverage Intent
    coverage_intent: Choice = Field(
        description="Coverage Intent",
        choices=[
            ("single_building", "Single Building"),
            ("campus_wide", "Campus-wide Coverage"),
            ("multi_site", "Multi-site Deployment"), 
            ("outdoor_coverage", "Outdoor Coverage"),
            ("high_density", "High Density Coverage")
        ]
    )
    
    # User Experience Intent
    user_experience: Choice = Field(
        description="Target User Experience",
        choices=[
            ("basic_connectivity", "Basic Connectivity"),
            ("standard_performance", "Standard Performance"),
            ("high_performance", "High Performance"),
            ("ultra_high_performance", "Ultra High Performance"),
            ("mission_critical", "Mission Critical")
        ],
        default="standard_performance"
    )
    
    # User Density Intent
    user_density: Choice = Field(
        description="Expected User Density",
        choices=[
            ("low", "Low (< 25 users per AP)"),
            ("medium", "Medium (25-50 users per AP)"),
            ("high", "High (50-100 users per AP)"),
            ("very_high", "Very High (100+ users per AP)")
        ],
        default="medium"
    )
    
    # Application Requirements
    application_types: List[Choice] = Field(
        description="Primary Application Types",
        choices=[
            ("web_email", "Web & Email"),
            ("video_streaming", "Video Streaming"),
            ("voice_calls", "Voice Calls (VoIP)"),
            ("video_conferencing", "Video Conferencing"),
            ("file_sharing", "Large File Sharing"),
            ("real_time_apps", "Real-time Applications"),
            ("iot_devices", "IoT Devices")
        ],
        default=["web_email"]
    )
    
    # Security Intent
    security_posture: Choice = Field(
        description="Security Posture",
        choices=[
            ("open_network", "Open Network"),
            ("basic_security", "Basic Security (WPA2-PSK)"),
            ("enterprise_security", "Enterprise Security (WPA2-Enterprise)"),
            ("high_security", "High Security (WPA3-Enterprise)"),
            ("zero_trust", "Zero Trust Security")
        ],
        default="enterprise_security"
    )
    
    # Guest Access Intent
    guest_access_required: bool = Field(
        description="Guest Access Required",
        default=True
    )
    
    guest_access_type: Choice = Field(
        description="Guest Access Type",
        choices=[
            ("open", "Open Guest Network"),
            ("captive_portal", "Captive Portal"),
            ("sponsored_access", "Sponsored Access"),
            ("self_service", "Self-service Registration")
        ],
        default="captive_portal",
        required=False
    )
    
    # Network Integration
    network_segmentation: Choice = Field(
        description="Network Segmentation Strategy",
        choices=[
            ("flat_network", "Flat Network"),
            ("vlan_segmentation", "VLAN Segmentation"),
            ("micro_segmentation", "Micro-segmentation"),
            ("zero_trust_segmentation", "Zero Trust Segmentation")
        ],
        default="vlan_segmentation"
    )
    
    # Site Selection
    target_sites: List[str] = Field(
        description="Target Site IDs",
        default=[]
    )
    
    # Advanced Intent
    enable_location_services: bool = Field(
        description="Enable Location Services",
        default=False
    )
    
    enable_analytics: bool = Field(
        description="Enable Advanced Analytics",
        default=True
    )
    
    bandwidth_optimization: bool = Field(
        description="Enable Bandwidth Optimization",
        default=True
    )
    
    roaming_optimization: bool = Field(
        description="Enable Roaming Optimization", 
        default=True
    )


class SiteWirelessForm(FormPage):
    """Site-specific wireless configuration"""
    site_id: str = Field(description="Mist Site ID")
    floor_plans: List[str] = Field(description="Floor Plan Files", default=[])
    ap_placement_strategy: Choice = Field(
        description="AP Placement Strategy",
        choices=[
            ("automatic", "Automatic (AI-driven)"),
            ("manual", "Manual Placement"),
            ("hybrid", "Hybrid (AI + Manual)")
        ],
        default="automatic"
    )
    expected_ap_count: int = Field(
        description="Expected AP Count",
        ge=1,
        le=1000,
        default=10
    )


@workflow("Deploy Wireless Network Service", target=Target.CREATE)
def deploy_wireless_service() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> analyze_wireless_intent
        >> discover_site_characteristics
        >> design_wireless_architecture
        >> optimize_rf_design
        >> create_mist_configuration
        >> deploy_access_points
        >> configure_wireless_policies
        >> optimize_ai_settings
        >> validate_wireless_coverage
        >> enable_monitoring_analytics
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate wireless service intent form"""
    return WirelessNetworkIntentForm


def analyze_wireless_intent(subscription: WirelessInactive) -> WirelessProvisioning:
    """Analyze wireless intent and translate to technical requirements"""
    subscription = WirelessProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    # Translate intent to technical requirements
    technical_requirements = {
        "rf_requirements": derive_rf_requirements(subscription.user_experience, subscription.user_density),
        "security_config": map_security_intent(subscription.security_posture),
        "qos_requirements": derive_qos_from_applications(subscription.application_types),
        "bandwidth_requirements": calculate_bandwidth_requirements(subscription.user_density, subscription.application_types),
        "ap_density": calculate_ap_density(subscription.user_density, subscription.coverage_intent),
        "roaming_config": derive_roaming_config(subscription.user_experience),
        "analytics_config": derive_analytics_config(subscription.enable_analytics)
    }
    
    subscription.technical_requirements = technical_requirements
    subscription.site_count = len(subscription.target_sites)
    
    return subscription


def discover_site_characteristics(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Discover site characteristics and existing infrastructure"""
    
    site_discovery = {
        "sites": [],
        "existing_infrastructure": {},
        "rf_environment": {},
        "capacity_requirements": {}
    }
    
    for site_id in subscription.target_sites:
        # Get site information from NetBox
        site_info = netbox.get_site(site_id)
        
        # Discover existing wireless infrastructure
        existing_aps = mist_client.get_site_devices(site_id, device_type="ap")
        existing_switches = netbox.get_site_devices(site_id, device_role="switch")
        
        site_characteristics = {
            "site_id": site_id,
            "site_name": site_info["name"],
            "site_type": site_info.get("custom_fields", {}).get("site_type", "office"),
            "floor_area_sqft": site_info.get("custom_fields", {}).get("floor_area", 10000),
            "building_construction": site_info.get("custom_fields", {}).get("construction_type", "standard"),
            "existing_aps": len(existing_aps),
            "available_switches": existing_switches,
            "power_available": assess_poe_availability(existing_switches),
            "estimated_users": estimate_user_count(site_info, subscription.user_density)
        }
        
        site_discovery["sites"].append(site_characteristics)
    
    # Analyze RF environment
    rf_scan_data = {
        "interference_sources": [],
        "channel_utilization": {},
        "neighboring_networks": []
    }
    
    site_discovery["rf_environment"] = rf_scan_data
    subscription.site_discovery = site_discovery
    
    return subscription


def design_wireless_architecture(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Design comprehensive wireless architecture"""
    
    architecture_design = {
        "network_design": {
            "ssid_configuration": design_ssid_architecture(subscription),
            "vlan_design": design_vlan_architecture(subscription),
            "security_design": design_security_architecture(subscription),
            "guest_network_design": design_guest_network(subscription) if subscription.guest_access_required else None
        },
        "rf_design": {
            "frequency_plan": "dual_band_optimized",  # 2.4GHz + 5GHz
            "channel_plan": "auto_optimized",
            "power_settings": "auto_optimized",
            "band_steering": True,
            "load_balancing": True
        },
        "qos_design": design_qos_policies(subscription),
        "roaming_design": design_roaming_policies(subscription)
    }
    
    subscription.architecture_design = architecture_design
    
    return subscription


def optimize_rf_design(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Optimize RF design using AI-driven planning"""
    
    callback_route = f"/api/workflows/wireless/deploy/{subscription.subscription_id}/rf_optimize"
    
    # Prepare RF optimization data
    rf_optimization_data = {
        "sites": subscription.site_discovery["sites"],
        "coverage_intent": subscription.coverage_intent,
        "user_density": subscription.user_density,
        "performance_target": subscription.user_experience,
        "application_requirements": subscription.application_types,
        "existing_rf_environment": subscription.site_discovery["rf_environment"]
    }
    
    # Use Mist AI for RF optimization
    optimization_result = mist_client.optimize_rf_design(rf_optimization_data)
    
    subscription.rf_optimization = optimization_result
    
    return subscription


def create_mist_configuration(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Create comprehensive Mist Cloud configuration"""
    
    # Create Mist organization if needed
    org_config = {
        "name": f"Orchestrator_{subscription.customer_id}",
        "settings": {
            "auto_upgrade": True,
            "analytics": subscription.enable_analytics,
            "location_services": subscription.enable_location_services
        }
    }
    
    mist_org_id = mist_client.get_or_create_organization(org_config)
    subscription.mist_org_id = mist_org_id
    
    # Create sites in Mist
    mist_sites = []
    for site_data in subscription.site_discovery["sites"]:
        mist_site = mist_client.create_site({
            "name": site_data["site_name"],
            "org_id": mist_org_id,
            "address": site_data.get("address", ""),
            "country_code": "US",
            "timezone": "America/New_York",
            "settings": {
                "auto_upgrade": {
                    "enabled": True,
                    "time_of_day": "02:00",
                    "day_of_week": "sun"
                }
            }
        })
        mist_sites.append(mist_site)
    
    subscription.mist_sites = mist_sites
    
    # Create WLAN configuration
    wlan_config = {
        "ssid": subscription.network_name,
        "enabled": True,
        "bands": ["2.4", "5"],
        "vlan_enabled": subscription.network_segmentation != "flat_network",
        "vlan_id": 100,  # Default, will be customized
        "auth": subscription.architecture_design["network_design"]["security_design"],
        "roam_mode": "11r" if subscription.roaming_optimization else "none",
        "band_steer": True,
        "airwatch": {
            "enabled": subscription.enable_analytics
        }
    }
    
    # Create guest WLAN if required
    guest_wlan_config = None
    if subscription.guest_access_required:
        guest_wlan_config = create_guest_wlan_config(subscription)
    
    subscription.wlan_configs = [wlan_config]
    if guest_wlan_config:
        subscription.wlan_configs.append(guest_wlan_config)
    
    return subscription


def deploy_access_points(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Deploy and configure access points"""
    
    callback_route = f"/api/workflows/wireless/deploy/{subscription.subscription_id}/deploy_aps"
    
    # Prepare AP deployment data
    ap_deployment_data = {
        "mist_org_id": subscription.mist_org_id,
        "sites": subscription.mist_sites,
        "rf_optimization": subscription.rf_optimization,
        "ap_models": determine_ap_models(subscription.technical_requirements),
        "power_requirements": "poe_plus",  # Determine based on AP model
        "adoption_mode": "automatic"
    }
    
    # Deploy APs using orchestrator automation
    execute_playbook(
        playbook_name="deploy_wireless_aps.yaml",
        callback_route=callback_route,
        inventory="mist-controller\n",
        extra_vars=ap_deployment_data
    )
    
    return subscription


def configure_wireless_policies(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Configure wireless policies and security"""
    
    # Apply WLAN configurations to all sites
    for site in subscription.mist_sites:
        for wlan_config in subscription.wlan_configs:
            mist_client.create_wlan(site["id"], wlan_config)
    
    # Configure RF policies
    rf_policies = {
        "band_steer": subscription.roaming_optimization,
        "client_limit": calculate_client_limit(subscription.user_density),
        "power_limit": "auto",
        "channel_width": "auto",
        "airtime_fairness": True
    }
    
    for site in subscription.mist_sites:
        mist_client.update_site_setting(site["id"], "rf", rf_policies)
    
    # Configure QoS policies
    qos_policies = subscription.architecture_design["qos_design"]
    for site in subscription.mist_sites:
        mist_client.configure_qos(site["id"], qos_policies)
    
    return subscription


def optimize_ai_settings(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Configure Mist AI optimization settings"""
    
    ai_settings = {
        "wifi_optimization": True,
        "wan_optimization": subscription.bandwidth_optimization,
        "switch_optimization": True,
        "marvis_actions": True,
        "anomaly_detection": True,
        "capacity_planning": subscription.enable_analytics,
        "user_engagement": subscription.enable_analytics,
        "location_analytics": subscription.enable_location_services
    }
    
    # Apply AI settings to organization
    mist_client.configure_ai_settings(subscription.mist_org_id, ai_settings)
    
    subscription.ai_optimization_enabled = True
    
    return subscription


def validate_wireless_coverage(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Validate wireless coverage and performance"""
    
    callback_route = f"/api/workflows/wireless/deploy/{subscription.subscription_id}/validate"
    
    validation_tests = {
        "coverage_tests": generate_coverage_tests(subscription),
        "performance_tests": generate_performance_tests(subscription),
        "roaming_tests": generate_roaming_tests(subscription) if subscription.roaming_optimization else [],
        "security_tests": generate_security_tests(subscription),
        "capacity_tests": generate_capacity_tests(subscription)
    }
    
    execute_playbook(
        playbook_name="validate_wireless_deployment.yaml",
        callback_route=callback_route,
        inventory="test-clients\n",
        extra_vars={
            "validation_tests": validation_tests,
            "mist_sites": subscription.mist_sites,
            "performance_targets": subscription.technical_requirements
        }
    )
    
    return subscription


def enable_monitoring_analytics(subscription: WirelessProvisioning) -> WirelessProvisioning:
    """Enable comprehensive monitoring and analytics"""
    
    monitoring_config = {
        "service_id": subscription.subscription_id,
        "service_name": subscription.network_name,
        "mist_org_id": subscription.mist_org_id,
        "sites": subscription.mist_sites,
        "monitoring_enabled": True,
        "analytics_enabled": subscription.enable_analytics,
        "alerting_config": {
            "performance_alerts": True,
            "security_alerts": True,
            "capacity_alerts": True,
            "anomaly_alerts": subscription.enable_analytics
        },
        "reporting_config": {
            "daily_reports": True,
            "weekly_summaries": True,
            "monthly_analytics": subscription.enable_analytics
        }
    }
    
    # Configure Mist insights and monitoring
    for site in subscription.mist_sites:
        mist_client.enable_insights(site["id"], {
            "wifi_health": True,
            "location_analytics": subscription.enable_location_services,
            "user_engagement": subscription.enable_analytics,
            "application_analytics": subscription.enable_analytics
        })
    
    subscription.monitoring_config = monitoring_config
    subscription.monitoring_enabled = True
    
    return subscription


# Helper functions
def derive_rf_requirements(user_experience: str, user_density: str) -> Dict:
    """Derive RF requirements from user experience and density"""
    requirements = {
        "basic_connectivity": {"min_rssi": -70, "max_co_channel": -60, "snr_threshold": 20},
        "standard_performance": {"min_rssi": -65, "max_co_channel": -65, "snr_threshold": 25}, 
        "high_performance": {"min_rssi": -60, "max_co_channel": -70, "snr_threshold": 30},
        "ultra_high_performance": {"min_rssi": -55, "max_co_channel": -75, "snr_threshold": 35},
        "mission_critical": {"min_rssi": -50, "max_co_channel": -80, "snr_threshold": 40}
    }
    
    base_req = requirements.get(user_experience, requirements["standard_performance"])
    
    # Adjust for density
    density_adjustments = {
        "high": {"min_rssi": base_req["min_rssi"] + 5, "snr_threshold": base_req["snr_threshold"] + 5},
        "very_high": {"min_rssi": base_req["min_rssi"] + 10, "snr_threshold": base_req["snr_threshold"] + 10}
    }
    
    if user_density in density_adjustments:
        base_req.update(density_adjustments[user_density])
    
    return base_req


def map_security_intent(security_posture: str) -> Dict:
    """Map security intent to technical configuration"""
    security_configs = {
        "open_network": {"type": "open"},
        "basic_security": {"type": "psk", "psk": "generated", "encryption": "wpa2"},
        "enterprise_security": {"type": "eap", "eap_type": "peap", "encryption": "wpa2"},
        "high_security": {"type": "eap", "eap_type": "tls", "encryption": "wpa3"},
        "zero_trust": {"type": "eap", "eap_type": "tls", "encryption": "wpa3", "additional_security": True}
    }
    return security_configs.get(security_posture, security_configs["enterprise_security"])


def derive_qos_from_applications(application_types: List[str]) -> Dict:
    """Derive QoS requirements from application types"""
    app_qos_map = {
        "web_email": {"priority": "bronze", "bandwidth": "low"},
        "video_streaming": {"priority": "silver", "bandwidth": "high"},
        "voice_calls": {"priority": "gold", "bandwidth": "medium", "latency_sensitive": True},
        "video_conferencing": {"priority": "gold", "bandwidth": "high", "latency_sensitive": True},
        "file_sharing": {"priority": "bronze", "bandwidth": "very_high"},
        "real_time_apps": {"priority": "platinum", "bandwidth": "medium", "latency_sensitive": True},
        "iot_devices": {"priority": "bronze", "bandwidth": "low"}
    }
    
    # Determine highest priority requirement
    priorities = ["bronze", "silver", "gold", "platinum"]
    max_priority = "bronze"
    high_bandwidth = False
    latency_sensitive = False
    
    for app in application_types:
        app_req = app_qos_map.get(app, {"priority": "bronze", "bandwidth": "low"})
        if priorities.index(app_req["priority"]) > priorities.index(max_priority):
            max_priority = app_req["priority"]
        if app_req["bandwidth"] in ["high", "very_high"]:
            high_bandwidth = True
        if app_req.get("latency_sensitive"):
            latency_sensitive = True
    
    return {
        "priority_class": max_priority,
        "high_bandwidth_required": high_bandwidth,
        "latency_sensitive": latency_sensitive
    }
