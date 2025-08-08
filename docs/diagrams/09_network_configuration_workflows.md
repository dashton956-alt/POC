# Network Configuration Workflows

## Overview
Flow diagrams for network configuration workflows including BGP, OSPF, QoS, VLAN management, and port channel configuration.

## 1. BGP Configuration Workflow

```mermaid
flowchart TD
    START[Start BGP Configuration]
    
    START --> FORM[BGP Configuration Form]
    FORM --> PARAMS{
        BGP Parameters
        Peer Configurations
        Routing Policies
        Target Devices
    }
    
    PARAMS --> VALIDATE_INPUT[Validate BGP Parameters]
    VALIDATE_INPUT --> VALID_INPUT{Parameters Valid?}
    
    VALID_INPUT -->|No| INPUT_ERROR[Parameter Validation Error]
    VALID_INPUT -->|Yes| DEVICE_SELECTION[Process Target Devices]
    
    subgraph "Per Device BGP Configuration"
        DEVICE[Target Device]
        NETBOX[Get Device Info from NetBox]
        PLATFORM[Check Platform Support]
        
        PLATFORM --> BGP_SUPPORT{BGP Supported?}
        BGP_SUPPORT -->|No| UNSUPPORTED[Platform Not Supported]
        BGP_SUPPORT -->|Yes| CONFIG_GEN[Generate BGP Configuration]
        
        CONFIG_GEN --> PEER_CONFIG[Configure BGP Peers]
        PEER_CONFIG --> POLICY_CONFIG[Apply Routing Policies]
        POLICY_CONFIG --> API_MGR[Centralized API Manager]
        
        API_MGR --> DEPLOY_BGP[Deploy BGP Configuration]
        DEPLOY_BGP --> DEPLOY_SUCCESS{Deployment Success?}
        
        DEPLOY_SUCCESS -->|No| DEPLOY_FAIL[Deployment Failed]
        DEPLOY_SUCCESS -->|Yes| VERIFY_BGP[Verify BGP Neighbors]
        
        VERIFY_BGP --> NEIGHBORS_UP{Neighbors Established?}
        NEIGHBORS_UP -->|No| BGP_TROUBLESHOOT[BGP Troubleshooting]
        NEIGHBORS_UP -->|Yes| BGP_SUCCESS[BGP Configuration Success]
    end
    
    DEVICE_SELECTION --> DEVICE
    NETBOX --> PLATFORM
    
    BGP_SUCCESS --> MORE_DEVICES{More Devices?}
    DEPLOY_FAIL --> MORE_DEVICES
    UNSUPPORTED --> MORE_DEVICES
    BGP_TROUBLESHOOT --> MORE_DEVICES
    
    MORE_DEVICES -->|Yes| DEVICE
    MORE_DEVICES -->|No| AGGREGATE[Aggregate Results]
    
    AGGREGATE --> VALIDATION[Validate BGP Topology]
    VALIDATION --> TOPOLOGY_OK{Topology Valid?}
    
    TOPOLOGY_OK -->|No| TOPOLOGY_ISSUES[Report Topology Issues]
    TOPOLOGY_OK -->|Yes| MONITORING[Setup BGP Monitoring]
    
    MONITORING --> REPORT[Generate Configuration Report]
    REPORT --> COMPLETE[BGP Configuration Complete]
    
    INPUT_ERROR --> END[End Workflow]
    TOPOLOGY_ISSUES --> END
    COMPLETE --> END

    classDef startEnd fill:#ff9999
    classDef process fill:#99ccff
    classDef decision fill:#ffcc99
    classDef error fill:#ffcdd2
    classDef success fill:#c8e6c9
    
    class START,END startEnd
    class FORM,VALIDATE_INPUT,DEVICE_SELECTION,NETBOX,CONFIG_GEN,PEER_CONFIG,POLICY_CONFIG,DEPLOY_BGP,VERIFY_BGP,AGGREGATE,VALIDATION,MONITORING,REPORT process
    class VALID_INPUT,BGP_SUPPORT,DEPLOY_SUCCESS,NEIGHBORS_UP,MORE_DEVICES,TOPOLOGY_OK decision
    class INPUT_ERROR,UNSUPPORTED,DEPLOY_FAIL,BGP_TROUBLESHOOT,TOPOLOGY_ISSUES error
    class BGP_SUCCESS,COMPLETE success
```

## 2. OSPF Configuration Workflow

```mermaid
flowchart TD
    START[Start OSPF Configuration]
    
    START --> FORM[OSPF Configuration Form]
    FORM --> PARAMS{
        OSPF Areas
        Interface Config
        Authentication
        Target Devices
    }
    
    PARAMS --> AREA_DESIGN[Validate OSPF Area Design]
    AREA_DESIGN --> AREA_VALID{Area Design Valid?}
    
    AREA_VALID -->|No| AREA_ERROR[Area Design Error]
    AREA_VALID -->|Yes| DEVICE_PROCESSING[Process Target Devices]
    
    subgraph "Per Device OSPF Configuration"
        DEVICE[Target Device]
        DEVICE_INFO[Get Device Info from NetBox]
        OSPF_CAPABLE[Check OSPF Capability]
        
        OSPF_CAPABLE --> CAPABLE{OSPF Supported?}
        CAPABLE -->|No| NOT_CAPABLE[Device Not Capable]
        CAPABLE -->|Yes| INTERFACE_CONFIG[Configure OSPF Interfaces]
        
        INTERFACE_CONFIG --> AREA_CONFIG[Configure OSPF Areas]
        AREA_CONFIG --> AUTH_CONFIG[Configure Authentication]
        AUTH_CONFIG --> API_MANAGER[Centralized API Manager]
        
        API_MANAGER --> DEPLOY_OSPF[Deploy OSPF Configuration]
        DEPLOY_OSPF --> DEPLOY_OK{Deployment Success?}
        
        DEPLOY_OK -->|No| OSPF_DEPLOY_FAIL[OSPF Deployment Failed]
        DEPLOY_OK -->|Yes| VERIFY_OSPF[Verify OSPF Neighbors]
        
        VERIFY_OSPF --> NEIGHBORS{Neighbors Formed?}
        NEIGHBORS -->|No| NEIGHBOR_ISSUES[Neighbor Formation Issues]
        NEIGHBORS -->|Yes| LSA_CHECK[Verify LSA Database]
        
        LSA_CHECK --> LSA_OK{LSA Database Consistent?}
        LSA_OK -->|No| LSA_ISSUES[LSA Consistency Issues]
        LSA_OK -->|Yes| OSPF_SUCCESS[OSPF Success]
    end
    
    DEVICE_PROCESSING --> DEVICE
    DEVICE_INFO --> OSPF_CAPABLE
    
    OSPF_SUCCESS --> MORE{More Devices?}
    OSPF_DEPLOY_FAIL --> MORE
    NOT_CAPABLE --> MORE
    NEIGHBOR_ISSUES --> MORE
    LSA_ISSUES --> MORE
    
    MORE -->|Yes| DEVICE
    MORE -->|No| CONVERGENCE[Check OSPF Convergence]
    
    CONVERGENCE --> CONVERGED{Network Converged?}
    CONVERGED -->|No| CONVERGENCE_ISSUES[Convergence Issues]
    CONVERGED -->|Yes| ROUTE_VERIFICATION[Verify Routing Tables]
    
    ROUTE_VERIFICATION --> ROUTES_OK{Routes Correct?}
    ROUTES_OK -->|No| ROUTING_ISSUES[Routing Table Issues]
    ROUTES_OK -->|Yes| MONITOR_SETUP[Setup OSPF Monitoring]
    
    MONITOR_SETUP --> COMPLETE[OSPF Configuration Complete]
    
    AREA_ERROR --> END[End Workflow]
    CONVERGENCE_ISSUES --> END
    ROUTING_ISSUES --> END
    COMPLETE --> END

    classDef startEnd fill:#ff9999
    classDef process fill:#99ccff
    classDef decision fill:#ffcc99
    classDef error fill:#ffcdd2
    classDef success fill:#c8e6c9
```

## 3. QoS Policy Configuration Workflow

```mermaid
flowchart TD
    START[Start QoS Configuration]
    
    START --> QOS_FORM[QoS Policy Form]
    QOS_FORM --> QOS_PARAMS{
        QoS Profiles
        Traffic Classes
        Bandwidth Allocation
        Target Devices
    }
    
    QOS_PARAMS --> POLICY_VALIDATION[Validate QoS Policies]
    POLICY_VALIDATION --> POLICY_VALID{Policies Valid?}
    
    POLICY_VALID -->|No| POLICY_ERROR[QoS Policy Error]
    POLICY_VALID -->|Yes| BANDWIDTH_CHECK[Check Bandwidth Availability]
    
    BANDWIDTH_CHECK --> BW_AVAILABLE{Bandwidth Available?}
    BW_AVAILABLE -->|No| BANDWIDTH_ERROR[Insufficient Bandwidth]
    BW_AVAILABLE -->|Yes| DEVICE_QOS[Process Each Device]
    
    subgraph "Per Device QoS Configuration"
        QOS_DEVICE[Target Device]
        QOS_INFO[Get Device QoS Capabilities]
        QOS_SUPPORT[Check QoS Feature Support]
        
        QOS_SUPPORT --> QOS_CAPABLE{QoS Supported?}
        QOS_CAPABLE -->|No| QOS_NOT_SUPPORTED[QoS Not Supported]
        QOS_CAPABLE -->|Yes| CLASS_MAPS[Configure Class Maps]
        
        CLASS_MAPS --> POLICY_MAPS[Configure Policy Maps]
        POLICY_MAPS --> INTERFACE_APPLY[Apply to Interfaces]
        INTERFACE_APPLY --> QOS_API[Centralized API Manager]
        
        QOS_API --> DEPLOY_QOS[Deploy QoS Configuration]
        DEPLOY_QOS --> QOS_DEPLOY_OK{Deployment Success?}
        
        QOS_DEPLOY_OK -->|No| QOS_DEPLOY_FAIL[QoS Deployment Failed]
        QOS_DEPLOY_OK -->|Yes| VERIFY_QOS[Verify QoS Implementation]
        
        VERIFY_QOS --> QOS_ACTIVE{QoS Policies Active?}
        QOS_ACTIVE -->|No| QOS_ACTIVATION_FAIL[QoS Activation Failed]
        QOS_ACTIVE -->|Yes| TRAFFIC_TEST[Test Traffic Shaping]
        
        TRAFFIC_TEST --> SHAPING_OK{Traffic Shaping Working?}
        SHAPING_OK -->|No| SHAPING_ISSUES[Traffic Shaping Issues]
        SHAPING_OK -->|Yes| QOS_SUCCESS[QoS Configuration Success]
    end
    
    DEVICE_QOS --> QOS_DEVICE
    QOS_INFO --> QOS_SUPPORT
    
    QOS_SUCCESS --> MORE_QOS{More Devices?}
    QOS_DEPLOY_FAIL --> MORE_QOS
    QOS_NOT_SUPPORTED --> MORE_QOS
    QOS_ACTIVATION_FAIL --> MORE_QOS
    SHAPING_ISSUES --> MORE_QOS
    
    MORE_QOS -->|Yes| QOS_DEVICE
    MORE_QOS -->|No| QOS_VALIDATION[Validate End-to-End QoS]
    
    QOS_VALIDATION --> E2E_OK{End-to-End QoS OK?}
    E2E_OK -->|No| E2E_ISSUES[End-to-End Issues]
    E2E_OK -->|Yes| QOS_MONITORING[Setup QoS Monitoring]
    
    QOS_MONITORING --> QOS_COMPLETE[QoS Configuration Complete]
    
    POLICY_ERROR --> END[End Workflow]
    BANDWIDTH_ERROR --> END
    E2E_ISSUES --> END
    QOS_COMPLETE --> END

    classDef startEnd fill:#ff9999
    classDef process fill:#99ccff
    classDef decision fill:#ffcc99
    classDef error fill:#ffcdd2
    classDef success fill:#c8e6c9
```

## 4. VLAN Management Workflow

```mermaid
flowchart TD
    START[Start VLAN Management]
    
    START --> OPERATION{VLAN Operation?}
    OPERATION -->|Create| CREATE_FORM[VLAN Creation Form]
    OPERATION -->|Delete| DELETE_FORM[VLAN Deletion Form]
    OPERATION -->|Modify| MODIFY_FORM[VLAN Modification Form]
    
    subgraph "VLAN Creation Flow"
        CREATE_FORM --> CREATE_PARAMS{
            VLAN ID
            VLAN Name
            Target Devices
            Interface Assignment
        }
        
        CREATE_PARAMS --> VLAN_VALIDATE[Validate VLAN Parameters]
        VLAN_VALIDATE --> ID_AVAILABLE{VLAN ID Available?}
        
        ID_AVAILABLE -->|No| ID_CONFLICT[VLAN ID Conflict]
        ID_AVAILABLE -->|Yes| CREATE_VLAN_LOOP[Create VLAN on Each Device]
        
        CREATE_VLAN_LOOP --> CREATE_DEVICE[Process Device]
        CREATE_DEVICE --> CREATE_API[Centralized API Manager]
        CREATE_API --> DEPLOY_CREATE[Deploy VLAN Creation]
        
        DEPLOY_CREATE --> CREATE_SUCCESS{Creation Success?}
        CREATE_SUCCESS -->|No| CREATE_FAILED[VLAN Creation Failed]
        CREATE_SUCCESS -->|Yes| ASSIGN_INTERFACES[Assign to Interfaces]
        
        ASSIGN_INTERFACES --> CREATE_NETBOX[Update NetBox VLAN]
        CREATE_NETBOX --> CREATE_COMPLETE[VLAN Creation Complete]
    end
    
    subgraph "VLAN Deletion Flow"
        DELETE_FORM --> DELETE_PARAMS{
            VLAN Selection
            Migration Options
            Safety Constraints
        }
        
        DELETE_PARAMS --> DEPENDENCY_CHECK[Analyze VLAN Dependencies]
        DEPENDENCY_CHECK --> DEPENDENCIES{Dependencies Found?}
        
        DEPENDENCIES -->|Yes| MIGRATION_REQUIRED[Interface Migration Required]
        DEPENDENCIES -->|No| SAFE_DELETE[Safe to Delete]
        
        MIGRATION_REQUIRED --> MIGRATE_INTERFACES[Migrate Interfaces]
        MIGRATE_INTERFACES --> SAFE_DELETE
        
        SAFE_DELETE --> DELETE_LOOP[Remove from Each Device]
        DELETE_LOOP --> DELETE_API[Centralized API Manager]
        DELETE_API --> DEPLOY_DELETE[Deploy VLAN Deletion]
        
        DEPLOY_DELETE --> DELETE_SUCCESS{Deletion Success?}
        DELETE_SUCCESS -->|No| DELETE_FAILED[VLAN Deletion Failed]
        DELETE_SUCCESS -->|Yes| CLEANUP_NETBOX[Cleanup NetBox Records]
        
        CLEANUP_NETBOX --> DELETE_COMPLETE[VLAN Deletion Complete]
    end
    
    CREATE_COMPLETE --> REPORT[Generate Report]
    DELETE_COMPLETE --> REPORT
    CREATE_FAILED --> REPORT
    DELETE_FAILED --> REPORT
    ID_CONFLICT --> REPORT
    
    REPORT --> END[End Workflow]

    classDef startEnd fill:#ff9999
    classDef process fill:#99ccff
    classDef decision fill:#ffcc99
    classDef error fill:#ffcdd2
    classDef success fill:#c8e6c9
```

## 5. Port Channel Configuration Workflow

```mermaid
flowchart TD
    START[Start Port Channel Configuration]
    
    START --> PC_FORM[Port Channel Form]
    PC_FORM --> PC_PARAMS{
        Interface Selection
        Bonding Parameters
        Load Balancing
        Target Devices
    }
    
    PC_PARAMS --> INTERFACE_VALIDATION[Validate Interface Selection]
    INTERFACE_VALIDATION --> INTERFACES_VALID{Interfaces Valid?}
    
    INTERFACES_VALID -->|No| INTERFACE_ERROR[Interface Validation Error]
    INTERFACES_VALID -->|Yes| COMPATIBILITY_CHECK[Check Interface Compatibility]
    
    COMPATIBILITY_CHECK --> COMPATIBLE{Interfaces Compatible?}
    COMPATIBLE -->|No| COMPATIBILITY_ERROR[Interface Compatibility Error]
    COMPATIBLE -->|Yes| PC_DEVICE_LOOP[Process Each Device]
    
    subgraph "Per Device Port Channel Configuration"
        PC_DEVICE[Target Device]
        PC_CAPABILITY[Check Port Channel Capability]
        
        PC_CAPABILITY --> PC_SUPPORT{Port Channel Supported?}
        PC_SUPPORT -->|No| PC_NOT_SUPPORTED[Port Channel Not Supported]
        PC_SUPPORT -->|Yes| PRE_CHECK[Pre-Configuration Checks]
        
        PRE_CHECK --> INTERFACES_FREE{Interfaces Free?}
        INTERFACES_FREE -->|No| INTERFACES_BUSY[Interfaces Already in Use]
        INTERFACES_FREE -->|Yes| PC_CONFIG[Configure Port Channel]
        
        PC_CONFIG --> MEMBER_CONFIG[Configure Member Interfaces]
        MEMBER_CONFIG --> LACP_CONFIG[Configure LACP/Bonding]
        LACP_CONFIG --> PC_API[Centralized API Manager]
        
        PC_API --> DEPLOY_PC[Deploy Port Channel Configuration]
        DEPLOY_PC --> PC_DEPLOY_OK{Deployment Success?}
        
        PC_DEPLOY_OK -->|No| PC_DEPLOY_FAIL[Port Channel Deployment Failed]
        PC_DEPLOY_OK -->|Yes| VERIFY_PC[Verify Port Channel Status]
        
        VERIFY_PC --> PC_UP{Port Channel Up?}
        PC_UP -->|No| PC_DOWN_ISSUES[Port Channel Down Issues]
        PC_UP -->|Yes| LOAD_BALANCE_TEST[Test Load Balancing]
        
        LOAD_BALANCE_TEST --> LB_OK{Load Balancing Working?}
        LB_OK -->|No| LB_ISSUES[Load Balancing Issues]
        LB_OK -->|Yes| PC_SUCCESS[Port Channel Success]
    end
    
    PC_DEVICE_LOOP --> PC_DEVICE
    PC_CAPABILITY --> PC_SUPPORT
    
    PC_SUCCESS --> MORE_PC{More Devices?}
    PC_DEPLOY_FAIL --> MORE_PC
    PC_NOT_SUPPORTED --> MORE_PC
    INTERFACES_BUSY --> MORE_PC
    PC_DOWN_ISSUES --> MORE_PC
    LB_ISSUES --> MORE_PC
    
    MORE_PC -->|Yes| PC_DEVICE
    MORE_PC -->|No| PC_FINAL_VALIDATION[Final Port Channel Validation]
    
    PC_FINAL_VALIDATION --> PC_FINAL_OK{All Port Channels OK?}
    PC_FINAL_OK -->|No| PC_FINAL_ISSUES[Port Channel Issues]
    PC_FINAL_OK -->|Yes| PC_MONITORING[Setup Port Channel Monitoring]
    
    PC_MONITORING --> PC_COMPLETE[Port Channel Configuration Complete]
    
    INTERFACE_ERROR --> END[End Workflow]
    COMPATIBILITY_ERROR --> END
    PC_FINAL_ISSUES --> END
    PC_COMPLETE --> END

    classDef startEnd fill:#ff9999
    classDef process fill:#99ccff
    classDef decision fill:#ffcc99
    classDef error fill:#ffcdd2
    classDef success fill:#c8e6c9
```

## Integration Patterns

### Common Integration Points
1. **Centralized API Manager**: All workflows use the centralized API management for optimal device connectivity
2. **NetBox Integration**: Device information, IP resolution, and status updates
3. **Configuration Validation**: Pre and post-deployment validation
4. **Error Handling**: Comprehensive error handling with rollback capabilities
5. **Monitoring Setup**: Automatic monitoring configuration for deployed features
6. **Concurrent Operations**: Parallel processing for multiple devices
7. **Platform Awareness**: Device platform-specific configuration generation

### Workflow Orchestration Features
- Form-based parameter collection
- Input validation and compatibility checking
- Device capability verification
- Configuration backup before changes
- Rollback mechanisms on failure
- Comprehensive reporting
- Status updates to NetBox
- Monitoring integration
