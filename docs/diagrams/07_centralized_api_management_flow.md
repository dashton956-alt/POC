# Centralized API Management Flow Diagram

## Overview
This diagram shows the centralized API management architecture and flow for device connectivity optimization.

```mermaid
graph TB
    subgraph "Workflow Layer"
        WF[Workflow Request]
        DEV[Device Selection]
        CFG[Configuration Data]
    end

    subgraph "Centralized API Management"
        API[API Manager]
        DC[Device Connector]
        
        subgraph "Platform Detection"
            PD[Platform Detection]
            OPT[Connection Optimization]
        end
        
        subgraph "Connection Methods"
            CC[Catalyst Center API]
            MC[Mist Cloud API]
            CVP[Arista CVP API]
            FM[FortiManager API]
            PAN[Panorama API]
            SSH[Direct SSH]
        end
    end

    subgraph "NetBox Integration"
        NB[NetBox IPAM/DCIM]
        IP[IP Resolution]
        CRED[Credential Management]
        PLAT[Platform Info]
    end

    subgraph "Network Devices"
        CISCO[Cisco Devices]
        JUNIPER[Juniper Devices]
        ARISTA[Arista Devices]
        FORTINET[Fortinet Devices]
        PALO[Palo Alto Devices]
        OTHER[Other Devices]
    end

    WF --> API
    DEV --> API
    CFG --> API
    
    API --> DC
    API --> NB
    
    NB --> IP
    NB --> CRED
    NB --> PLAT
    
    DC --> PD
    PD --> OPT
    
    OPT --> CC
    OPT --> MC
    OPT --> CVP
    OPT --> FM
    OPT --> PAN
    OPT --> SSH
    
    CC --> CISCO
    MC --> JUNIPER
    CVP --> ARISTA
    FM --> FORTINET
    PAN --> PALO
    SSH --> OTHER
    SSH --> CISCO
    SSH --> JUNIPER
    SSH --> ARISTA

    classDef apiLayer fill:#e1f5fe
    classDef netboxLayer fill:#f3e5f5
    classDef deviceLayer fill:#e8f5e8
    
    class API,DC,PD,OPT,CC,MC,CVP,FM,PAN,SSH apiLayer
    class NB,IP,CRED,PLAT netboxLayer
    class CISCO,JUNIPER,ARISTA,FORTINET,PALO,OTHER deviceLayer
```

## Connection Priority Logic

```mermaid
flowchart TD
    START[Device Connection Request]
    
    START --> NETBOX[Get Device Info from NetBox]
    NETBOX --> PLATFORM{Device Platform?}
    
    PLATFORM -->|Cisco| CISCO_CHECK{Catalyst Center Available?}
    PLATFORM -->|Juniper| MIST_CHECK{Mist Cloud Available?}
    PLATFORM -->|Arista| CVP_CHECK{CVP Available?}
    PLATFORM -->|Fortinet| FORTI_CHECK{FortiManager Available?}
    PLATFORM -->|Palo Alto| PAN_CHECK{Panorama Available?}
    PLATFORM -->|Unknown/Other| SSH_FALLBACK[Direct SSH Connection]
    
    CISCO_CHECK -->|Yes| CATALYST_API[Use Catalyst Center API]
    CISCO_CHECK -->|No| SSH_FALLBACK
    
    MIST_CHECK -->|Yes| MIST_API[Use Mist Cloud API]
    MIST_CHECK -->|No| SSH_FALLBACK
    
    CVP_CHECK -->|Yes| CVP_API[Use Arista CVP API]
    CVP_CHECK -->|No| SSH_FALLBACK
    
    FORTI_CHECK -->|Yes| FORTI_API[Use FortiManager API]
    FORTI_CHECK -->|No| SSH_FALLBACK
    
    PAN_CHECK -->|Yes| PAN_API[Use Panorama API]
    PAN_CHECK -->|No| SSH_FALLBACK
    
    CATALYST_API --> EXECUTE[Execute Configuration]
    MIST_API --> EXECUTE
    CVP_API --> EXECUTE
    FORTI_API --> EXECUTE
    PAN_API --> EXECUTE
    SSH_FALLBACK --> EXECUTE
    
    EXECUTE --> SUCCESS{Success?}
    SUCCESS -->|Yes| COMPLETE[Operation Complete]
    SUCCESS -->|No| RETRY{Retry Available?}
    
    RETRY -->|Yes| FALLBACK[Try Next Method]
    RETRY -->|No| FAIL[Operation Failed]
    
    FALLBACK --> SSH_FALLBACK

    classDef startEnd fill:#ff9999
    classDef decision fill:#ffcc99
    classDef process fill:#99ccff
    classDef api fill:#99ff99
    
    class START,COMPLETE,FAIL startEnd
    class PLATFORM,CISCO_CHECK,MIST_CHECK,CVP_CHECK,FORTI_CHECK,PAN_CHECK,SUCCESS,RETRY decision
    class NETBOX,EXECUTE,FALLBACK process
    class CATALYST_API,MIST_API,CVP_API,FORTI_API,PAN_API,SSH_FALLBACK api
```

## API Manager Configuration

```mermaid
graph LR
    subgraph "Environment Configuration"
        ENV[Environment Variables]
        
        subgraph "API Endpoints"
            CC_URL[CATALYST_CENTER_URL]
            MC_URL[MIST_CLOUD_URL] 
            CVP_URL[ARISTA_CVP_URL]
            FM_URL[FORTIMANAGER_URL]
            PAN_URL[PANORAMA_URL]
        end
        
        subgraph "Authentication"
            CC_TOKEN[CATALYST_CENTER_TOKEN]
            MC_TOKEN[MIST_CLOUD_TOKEN]
            CVP_TOKEN[ARISTA_CVP_TOKEN]
            FM_TOKEN[FORTIMANAGER_TOKEN]
            PAN_TOKEN[PANORAMA_TOKEN]
        end
    end
    
    subgraph "API Manager"
        MANAGER[API Manager Instance]
        CONFIG[Configuration Loader]
        VALIDATE[Endpoint Validation]
    end
    
    ENV --> MANAGER
    CC_URL --> CONFIG
    MC_URL --> CONFIG
    CVP_URL --> CONFIG
    FM_URL --> CONFIG
    PAN_URL --> CONFIG
    
    CC_TOKEN --> CONFIG
    MC_TOKEN --> CONFIG
    CVP_TOKEN --> CONFIG
    FM_TOKEN --> CONFIG
    PAN_TOKEN --> CONFIG
    
    CONFIG --> VALIDATE
    VALIDATE --> MANAGER

    classDef envVars fill:#fff2cc
    classDef apiManager fill:#d5e8d4
    
    class ENV,CC_URL,MC_URL,CVP_URL,FM_URL,PAN_URL,CC_TOKEN,MC_TOKEN,CVP_TOKEN,FM_TOKEN,PAN_TOKEN envVars
    class MANAGER,CONFIG,VALIDATE apiManager
```
