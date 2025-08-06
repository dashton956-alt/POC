# Add your plugins and plugin settings here.
# Of course uncomment this file out.

# To learn how to build images with your required plugins
# See https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins

PLUGINS = ["netbox_secrets",
#"netbox_config_diff",
"netbox_topology_views",
"netbox_lists",
"validity",
"netbox_routing",
"netbox_branching"]


#PLUGINS_CONFIG = {
#    "netbox_config_diff": {
#        'USERNAME' "admin",
#        'PASSWORD' "admin",
#        "AUTH_SECONDARY": "admin",  # define here password for accessing Privileged EXEC mode, this variable is optional
#    },
#}
PLUGINS_CONFIG = {
    'netbox_topology_views': {
        'static_image_directory': 'netbox_topology_views/img',
        'allow_coordinates_saving': True,
        'always_save_coordinates': True
    }
}
PLUGINS_CONFIG = {
    "netbox_lists": {
        # Return IPs as /32 or /128.
        # Default: True
        "as_cidr": True,
        # For services without any explicit IPs configured,
        # use the primary IPs of the associated device/vm.
        # Default: True
        "service_primary_ips": True,
        # Summarize responses
        "summarize": True,
        # A list of attributes for the devices-vms-attrs endpoint
        #
        # Attributes will be joined with "__" in the returned object.
        # eg. ("primary_ip", "address") -> primary_ip__address
        "devices_vms_attrs": [
            ("id",),
            ("name",),
            ("role", "slug"),
            ("platform", "slug"),
            ("primary_ip", "address"),
            ("tags",),
        ],
        # Tuple/list of attributes to use for Prometheus VM SD target. Defaults are shown.
        #
        # If all attributes return None, the device's name will be used.
        "prometheus_vm_sd_target": (
            # For a custom field
            # ("cf", "fqdn"),
            # If this returns none, try Name.
            ("primary_ip", "address", "ip"),
            ("name",), # not necessary
        ),
        # Dictionary of label to VM attribute for Prometheus VM SD. Defaults are shown.
        "prometheus_vm_sd_labels": {
            "__meta_netbox_id": ("id",),
            "__meta_netbox_name": ("name",),
            "__meta_netbox_status": ("status",),
            "__meta_netbox_cluster_name": ("cluster", "name"),
            "__meta_netbox_site_name": ("site", "name"),
            "__meta_netbox_role_name": ("role", "name"),
            "__meta_netbox_platform_name": ("platform", "name"),
            "__meta_netbox_primary_ip": ("primary_ip", "address", "ip"),
            "__meta_netbox_primary_ip4": ("primary_ip4", "address", "ip"),
            "__meta_netbox_primary_ip6": ("primary_ip6", "address", "ip"),
            # A custom field. Will be an empty string if None.
            # "__meta_netbox_fqdn": ("cf", "fqdn"),
        },
        # Tuple/list of attributes to use for Prometheus device SD target. Defaults are shown.
        #
        # If all attributes return None, the device's name will be used.
        "prometheus_device_sd_target": (
            # For a custom field
            # ("cf", "fqdn"),
            ("primary_ip", "address", "ip"),
            ("name",), # not necessary
        ),
        # Dictionary of label to device attribute for Prometheus device SD. Defaults are shown.
        "prometheus_device_sd_labels": {
            "__meta_netbox_id": ("id",),
            "__meta_netbox_name": ("name",),
            "__meta_netbox_status": ("status",),
            "__meta_netbox_site_name": ("site", "name"),
            "__meta_netbox_platform_name": ("platform", "name"),
            "__meta_netbox_primary_ip": ("primary_ip", "address", "ip"),
            "__meta_netbox_primary_ip4": ("primary_ip4", "address", "ip"),
            "__meta_netbox_primary_ip6": ("primary_ip6", "address", "ip"),
            "__meta_netbox_serial": ("serial",),
            # A custom field. Will be an empty string if None.
            # "__meta_netbox_fqdn": ("cf", "fqdn"),
        },
        # Tuple/list of attributes to use for Prometheus IP address SD target. Defaults are shown.
        #
        # If all attributes return None, the address in CIDR format will be used.
        "prometheus_ipaddress_sd_target": (
            ("address", "ip"),
        ),
        # Dictionary of label to IP address attribute for Prometheus ip address SD. Defaults are shown.
        "prometheus_ipaddress_sd_labels": {
            "__meta_netbox_id": ("id",),
            "__meta_netbox_role": ("role",),
            "__meta_netbox_dns_name": ("dns_name",),
            "__meta_netbox_status": ("status",),
            # For addresses assigned to interfaces
            #"__meta_netbox_device": ("assigned_object", "device", "name"),
            #"__meta_netbox_interface": ("assigned_object", "name"),
        },
    }
}