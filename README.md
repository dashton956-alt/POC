# Intent Based Orchestrator with Centralized API Management

A comprehensive Intent-Based Networking (IBN) platform featuring **centralized API management** with multi-vendor network automation. This advanced system combines NetBox DCIM, orchestrated workflows, and intelligent device connectivity to provide enterprise-grade network infrastructure management.

## 🎯 New Centralized API Management System

### 🌐 Multi-Vendor Platform Support
- **Cisco Catalyst Center**: Enterprise DNA Center API integration
- **Juniper Mist Cloud**: AI-driven network operations platform
- **Arista CloudVision**: Network-wide workload orchestration
- **Fortinet FortiManager**: Centralized security management
- **Palo Alto Panorama**: Unified firewall management
- **Direct SSH Fallback**: Universal device access for any platform

### 🔄 Intelligent Connection Optimization
- **Platform-Aware Routing**: Automatic optimal API method selection
- **NetBox IP Resolution**: Dynamic device IP retrieval from IPAM
- **Fallback Mechanisms**: Automatic SSH fallback when APIs unavailable
- **Concurrent Operations**: Async deployment for improved performance
- **Connection Pooling**: Efficient resource management and reuse

### 📋 Comprehensive Workflow Coverage
- **Device Lifecycle**: Discovery, onboarding, bootstrap configuration, health checks
- **Network Configuration**: BGP, OSPF, QoS, VLAN management, port channels
- **Infrastructure Management**: Vendor imports, device types, NetBox integration
- **Multi-Vendor Operations**: Concurrent configuration across different platforms
- **Monitoring & Observability**: Network monitoring setup and health assessment

## ✨ Enhanced Dashboard Features

### 🎨 Professional Web Interface
- **Modern Dashboard**: Comprehensive system overview with real-time statistics
- **System Status**: Live monitoring of orchestrator engine, NetBox DCIM, and UI services
- **NetBox Integration**: Direct integration showing manufacturers, device types, and devices
- **Responsive Design**: Mobile-friendly interface with professional styling

### 🔧 Advanced Workflow Management
- **Organized Categories**: Workflows grouped by function (Device Lifecycle, Network Configuration, Infrastructure)
- **Infrastructure as Code (IaC)**: Automated infrastructure provisioning workflows
- **Intent Based Networking**: Intelligent network automation with policy-driven configuration
- **Quick Actions**: One-click access to common network operations

### 📊 Real-time Monitoring & Analytics
- **Auto-refresh Statistics**: NetBox data updates every 30 seconds
- **System Health Checks**: Comprehensive connectivity and performance monitoring  
- **Visual Status Indicators**: Animated status indicators with pulse effects
- **Centralized API Status**: Live monitoring of all platform API connections

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Git
- 8GB+ RAM recommended

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dashton956-alt/POC.git
   cd POC
   ```

2. **Configure Centralized API Management**
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   
   # Edit .env file with your API endpoints:
   # CATALYST_CENTER_URL=https://your-catalyst-center.domain
   # CATALYST_CENTER_TOKEN=your_api_token
   # MIST_CLOUD_URL=https://api.mist.com
   # MIST_CLOUD_TOKEN=your_mist_token
   # ARISTA_CVP_URL=https://your-cvp.domain
   # ARISTA_CVP_TOKEN=your_cvp_token
   # FORTIMANAGER_URL=https://your-fortimanager.domain
   # FORTIMANAGER_TOKEN=your_fortimanager_token
   # PANORAMA_URL=https://your-panorama.domain
   # PANORAMA_TOKEN=your_panorama_token
   ```

3. **Start NetBox Services**
   ```bash
   cd netbox
   docker-compose up -d
   ```

4. **Start Orchestrator with Centralized API Management**
   ```bash
   cd ../example-orchestrator
   docker-compose up -d
   ```

5. **Import Network Device Data**
   
   **Option A: Enhanced Web Dashboard (Recommended)**
   ```bash
   # Open http://localhost:3000/dashboard.html in your browser
   # Navigate to "Infrastructure Workflows" and run:
   # - Import Vendors (import manufacturers)
   # - Import Device Types (import device type definitions)
   ```
   
   **Option B: Command Line**
   ```bash
   make import-all-devicetypes    # Import vendors + device types
   # OR use individual scripts:
   python3 vendor_import.py       # Import vendors/manufacturers
   python3 device_type_import.py --limit 50  # Import device types
   ```

6. **Access the Applications**
   - **🎯 Enhanced Dashboard**: http://localhost:3000/dashboard.html ⭐ **NEW**
   - **📋 Workflow Interface**: http://localhost:3000 
   - **🔧 NetBox DCIM**: http://localhost:8000
   - **🔌 Orchestrator API**: http://localhost:8080

## 🔧 Centralized API Management Configuration

### Environment Variables

The system uses environment variables to configure API endpoints for different network platforms:

```bash
# Cisco Catalyst Center (DNA Center)
CATALYST_CENTER_URL=https://your-catalyst-center.domain
CATALYST_CENTER_TOKEN=your_api_token
CATALYST_CENTER_USERNAME=admin
CATALYST_CENTER_PASSWORD=your_password

# Juniper Mist Cloud
MIST_CLOUD_URL=https://api.mist.com
MIST_CLOUD_TOKEN=your_mist_cloud_token
MIST_ORG_ID=your_organization_id

# Arista CloudVision Platform
ARISTA_CVP_URL=https://your-cvp.domain
ARISTA_CVP_TOKEN=your_cvp_token
ARISTA_CVP_USERNAME=admin
ARISTA_CVP_PASSWORD=your_password

# Fortinet FortiManager
FORTIMANAGER_URL=https://your-fortimanager.domain
FORTIMANAGER_TOKEN=your_fortimanager_token
FORTIMANAGER_USERNAME=admin
FORTIMANAGER_PASSWORD=your_password

# Palo Alto Panorama
PANORAMA_URL=https://your-panorama.domain
PANORAMA_TOKEN=your_panorama_api_key
PANORAMA_USERNAME=admin
PANORAMA_PASSWORD=your_password

# NetBox Configuration
NETBOX_URL=http://netbox:8000
NETBOX_TOKEN=your_netbox_token

# SSH Fallback Configuration
DEFAULT_SSH_USERNAME=admin
DEFAULT_SSH_PASSWORD=your_ssh_password
SSH_TIMEOUT=30
```

### API Endpoint Priority

The system automatically selects the optimal connection method based on device platform:

1. **Platform-Specific API** (Preferred)
2. **Direct SSH Connection** (Fallback)
3. **Telnet Connection** (Last resort)

This ensures maximum compatibility while optimizing for API-based management when available.
   - **API Documentation**: http://localhost:8080/api/docs

   **🎯 Recommended Starting Point**: Visit the **Enhanced Dashboard** for a complete overview of your system!

## 📋 Project Structure

```
POC/
├── netbox/                     # NetBox IPAM/DCIM platform
│   ├── docker-compose.yml     # NetBox container orchestration
│   ├── configuration/         # NetBox configuration files
│   └── ...
├── example-orchestrator/       # Custom orchestrator service
│   ├── docker-compose.yml     # Orchestrator container setup
│   ├── workflows/             # Automation workflows
│   ├── products/              # Product definitions
│   └── services/              # Integration services
├── devicetype-library/         # NetBox device type definitions
│   ├── device-types/          # Device type YAML files
│   ├── module-types/          # Module type definitions
│   └── schema/                # Validation schemas
├── device_import.py           # Device type import script
└── README.md                  # This file
```

## 🛠️ Components

### Enhanced Orchestrator UI ⭐ **NEW**
- **Purpose**: Modern web dashboard with comprehensive system management
- **Ports**: 3000 (Main UI), 3000/dashboard.html (Enhanced Dashboard)
- **Features**: 
  - Real-time system status monitoring
  - NetBox integration with live statistics
  - Workflow management with categorized navigation
  - Professional responsive design with animations
  - Auto-refresh functionality (30-second intervals)
  - Quick actions for common operations
  - Infrastructure as Code (IAC) workflow support
  - Intent-based networking automation
- **Technologies**: HTML5, CSS3, JavaScript (ES6+), Responsive Grid

### NetBox DCIM
- **Purpose**: Network documentation and Infrastructure Management
- **Port**: 8000
- **Features**: Device inventory, IP management, circuit tracking, manufacturer data
- **Database**: PostgreSQL
- **Cache**: Redis (port 6379)
- **Integration**: Seamlessly integrated with orchestrator dashboard

### Orchestrator Engine
- **Purpose**: Workflow automation and service orchestration
- **Port**: 8080 (API), 3000 (UI)
- **Features**: 
  - GraphQL API with comprehensive endpoints
  - Workflow engine with real-time execution
  - NetBox integration with enhanced APIs
  - Dashboard data endpoints for UI
  - System health monitoring
- **Database**: PostgreSQL
- **Cache**: Redis (port 6380)

### Device Type Library
- **Purpose**: Standardized device definitions
- **Content**: 8000+ device types from major vendors
- **Format**: YAML with JSON schema validation
- **Vendors**: Cisco, Juniper, Arista, HP, Dell, and many more

## 🔧 Configuration

### Environment Variables

#### NetBox (.env)
```bash
NETBOX_SECRET_KEY=your-secret-key
DB_PASSWORD=netbox-db-password
REDIS_PASSWORD=redis-password
```

#### Orchestrator (.env)
```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/orchestrator
REDIS_URL=redis://redis:6380
NETBOX_URL=http://netbox:8080
NETBOX_TOKEN=your-netbox-api-token
```

### Network Configuration

The project uses Docker networks to enable communication between services:

- **NetBox Network**: `netbox_default`
- **Orchestrator Network**: `orchestrator_default`
- **Shared Network**: Services communicate via exposed ports

### Redis Port Configuration

To avoid conflicts, Redis instances use different ports:
- NetBox Redis: 6379
- Orchestrator Redis: 6380

## 📚 Usage

### 🎨 Enhanced Web Dashboard **NEW**

#### Accessing the Dashboard
```bash
# Open the enhanced dashboard in your browser
open http://localhost:3000/dashboard.html

# Or use the welcome page
open http://localhost:3000
```

#### Dashboard Features
- **System Status**: Monitor all services with live status indicators
- **NetBox Statistics**: Real-time counts of manufacturers, device types, and devices  
- **Quick Actions**: One-click access to common operations
- **Centralized API Management**: Multi-vendor platform integration status
- **Workflow Categories**: Organized workflow navigation with 13+ comprehensive workflows
- **Auto-refresh**: Automatic updates every 30 seconds

## 🔄 Comprehensive Workflow Categories

### 1. **Infrastructure Management**
   - **Vendor Import**: Import network device manufacturers from devicetype-library
   - **Device Type Import**: Import device definitions with platform-specific details
   - **NetBox Bootstrap**: Initialize NetBox with essential configuration
   - **NetBox Data Management**: Clean up and manage NetBox data

### 2. **Device Lifecycle Management** ⭐ **NEW**
   - **Device Discovery**: Auto-discover devices via SNMP, LLDP, CDP with platform detection
   - **Device Onboarding**: Complete device provisioning and NetBox integration
   - **Bootstrap Configuration**: Apply day-0 configuration with site-aware templates
   - **Device Health Check**: Comprehensive device validation and health assessment
   - **Configuration Template Deployment**: Apply standardized configurations using templates

### 3. **Network Configuration Workflows** ⭐ **NEW**
   - **BGP Configuration**: Configure Border Gateway Protocol with peer management
   - **OSPF Configuration**: Configure Open Shortest Path First routing with area management
   - **QoS Policy Configuration**: Implement Quality of Service policies with traffic shaping
   - **VLAN Management**: Create, modify, and manage VLANs with dependency analysis
   - **VLAN Deletion**: Safely remove VLANs with interface migration capabilities
   - **Port Channel Configuration**: Configure link aggregation with load balancing

### 4. **Monitoring & Observability** ⭐ **NEW**
   - **Network Monitoring Setup**: Deploy comprehensive monitoring with SNMP configuration
   - **Performance Baseline Creation**: Establish network performance baselines
   - **Alert Configuration**: Setup automated alerting with threshold management

### 5. **Multi-Vendor Operations** ⭐ **NEW**
   - **Multi-Vendor Network Configuration**: Comprehensive workflow demonstrating centralized API management across:
     - **Cisco Catalyst Center**: Enterprise DNA Center integration
     - **Juniper Mist Cloud**: AI-driven network operations
     - **Arista CloudVision**: Network workload orchestration  
     - **Fortinet FortiManager**: Security-focused management
     - **Palo Alto Panorama**: Unified firewall management
     - **Direct SSH Fallback**: Universal device support

### 6. **Infrastructure as Code (IaC)**
   - **Automated Infrastructure Provisioning**: Template-driven infrastructure deployment
   - **Configuration Drift Detection**: Monitor and remediate configuration changes
   - **Policy Compliance Checking**: Automated compliance validation
   - **Version-Controlled Configurations**: Git-based configuration management

### 7. **Intent Based Networking**
   - **Intelligent Network Automation**: AI-driven network optimization
   - **Policy-Driven Configuration**: Intent-based policy enforcement
   - **Network Intent Validation**: Automated intent verification and remediation

## 🔧 Centralized API Management Features

### Platform Integration Status
- ✅ **Cisco Catalyst Center**: Full API integration with intelligent device management
- ✅ **Juniper Mist Cloud**: AI-powered network operations integration  
- ✅ **Arista CVP**: CloudVision Platform integration for data center networks
- ✅ **Fortinet FortiManager**: Security-focused centralized management
- ✅ **Palo Alto Panorama**: Unified firewall policy management
- ✅ **Direct SSH Fallback**: Universal compatibility for any network device

### Intelligent Connection Management
- **NetBox IP Resolution**: Automatic device IP retrieval from IPAM
- **Platform Detection**: Automatic device platform identification
- **Optimal API Selection**: Intelligent selection of best connection method
- **Fallback Mechanisms**: Automatic SSH fallback when APIs unavailable
- **Connection Pooling**: Efficient resource management and connection reuse
- **Concurrent Operations**: Parallel device operations for improved performance

### 1. NetBox Operations

#### Create a Site
```python
import pynetbox
nb = pynetbox.api('http://localhost:8000', token='your-token')
site = nb.dcim.sites.create(name='datacenter-01', slug='dc01')
```

#### Add Devices
```python
device_type = nb.dcim.device_types.get(model='catalyst-9300-48p')
device = nb.dcim.devices.create(
    name='switch-01',
    device_type=device_type.id,
    site=site.id
)
```

### 2. Enhanced Orchestrator Workflows **NEW**

#### Using the Web Dashboard
```bash
# Access the enhanced dashboard
http://localhost:3000/dashboard.html

# Navigate to Available Workflows section
# Click on any workflow category to access workflows
```

#### Quick Actions from Dashboard
- **Import Device Types**: Direct access to device library import
- **NetBox DCIM**: Quick link to NetBox interface  
- **API Documentation**: Access to comprehensive API docs
- **System Health Check**: One-click system status verification

#### Enhanced API Endpoints **NEW**
```bash
# Get dashboard statistics
curl http://localhost:8080/api/dashboard/netbox-stats

# Get system status
curl http://localhost:8080/api/system-status

# Get workflow categories  
curl http://localhost:8080/api/workflows/categories

# Search NetBox devices
curl http://localhost:8080/api/netbox/search?q=cisco
```

#### Create Node Workflow
```bash
curl -X POST http://localhost:8080/api/workflows/node/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "core-router-01",
    "location": "datacenter-01",
    "device_type": "cisco-asr-9000"
  }'
```

#### GraphQL Query Example
```graphql
query {
  nodes {
    id
    name
    status
    ports {
      name
      type
      status
    }
  }
}
```

### 3. Device Import

The `device_import.py` script imports device types from the library:

```bash
# Import all device types
python device_import.py

# Import specific vendor
python device_import.py --vendor cisco

# Dry run (no actual import)
python device_import.py --dry-run
```

## 🔍 Monitoring and Troubleshooting

### 🎨 Enhanced Dashboard Monitoring **NEW**

#### System Status Dashboard
```bash
# Access the comprehensive system status
http://localhost:3000/dashboard.html

# Features:
# - Live status indicators with pulse animations
# - Real-time NetBox statistics
# - Auto-refresh every 30 seconds  
# - Visual health indicators
# - Quick action buttons
```

#### Dashboard Health Checks
The enhanced dashboard provides:
- **Orchestrator Engine Status**: Real-time connectivity to API (port 8080)
- **NetBox DCIM Status**: Live connection monitoring (port 8000)  
- **UI Status**: Current interface status (port 3000)
- **Statistics Monitoring**: Manufacturers, device types, and device counts
- **Error Handling**: Graceful fallbacks with informative messages

### Traditional Health Checks

```bash
# Check all container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check orchestrator health (Enhanced API)
curl http://localhost:8080/api/system-status

# Check NetBox health
curl http://localhost:8000/api/status/

# Check enhanced dashboard APIs
curl http://localhost:8080/api/dashboard/netbox-stats
curl http://localhost:8080/api/dashboard/system-status
```

### Common Issues

#### Redis Connection Errors
```bash
# Check Redis connectivity
docker exec -it netbox-redis-1 redis-cli ping
docker exec -it redis redis-cli -p 6380 ping
```

#### Database Issues
```bash
# Check PostgreSQL status
docker exec -it netbox-postgres-1 pg_isready
docker exec -it postgres psql -U orchestrator -d orchestrator -c "SELECT 1;"
```

#### Enhanced UI Issues **NEW**
```bash
# Dashboard not loading
# Check if orchestrator-ui container is running
docker ps | grep orchestrator-ui

# Dashboard shows connection errors
# Verify API endpoints are accessible
curl http://localhost:8080/api/dashboard/netbox-stats

# Statistics not updating
# Check browser console for JavaScript errors
# Verify auto-refresh is functioning (30-second intervals)

# Workflow navigation not working  
# Check that orchestrator API is responding
curl http://localhost:8080/api/workflows/categories
```
#### Port Conflicts
```bash
# Check port usage (Enhanced ports)
ss -tulpn | grep :3000   # Enhanced Dashboard  
ss -tulpn | grep :8000   # NetBox DCIM
ss -tulpn | grep :8080   # Orchestrator API

# If port 3000 is occupied, check what's using it
lsof -i :3000
```

### Log Access

```bash
# Enhanced UI logs
docker logs orchestrator-ui

# NetBox logs  
docker logs netbox-netbox-1

# Orchestrator logs (Enhanced APIs)
docker logs orchestrator

# Redis logs
docker logs redis

# View enhanced dashboard API logs
docker logs orchestrator | grep "api/dashboard"
```

## 🚀 Development

### Setting Up Development Environment

1. **Clone and Setup**
   ```bash
   git clone https://github.com/dashton956-alt/POC.git
   cd POC
   ```

2. **Virtual Environment** (for device_import.py)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Development Containers**
   ```bash
   # NetBox development mode
   cd netbox
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

   # Orchestrator development mode
   cd ../example-orchestrator
   docker-compose up -d
   ```

### Code Structure

#### NetBox Integration
- `services/netbox.py`: NetBox API client
- `products/services/netbox/`: NetBox-specific services
- `device_import.py`: Device type import utility

#### Orchestrator Workflows
- `workflows/node/`: Node management workflows
- `workflows/port/`: Port configuration workflows
- `workflows/core_link/`: Link provisioning workflows
- `workflows/l2vpn/`: L2VPN service workflows

#### Product Definitions
- `products/product_types/`: Service product definitions
- `products/product_blocks/`: Reusable product components

### API Documentation

#### Enhanced API Documentation **NEW**

##### Dashboard APIs
- **System Status**: http://localhost:8080/api/system-status
- **NetBox Statistics**: http://localhost:8080/api/dashboard/netbox-stats  
- **Dashboard Data**: http://localhost:8080/api/dashboard/statistics
- **Import Status**: http://localhost:8080/api/dashboard/import-status

##### NetBox Integration APIs  
- **Manufacturer Summary**: http://localhost:8080/api/netbox/manufacturers
- **Device Search**: http://localhost:8080/api/netbox/search?q=QUERY
- **Workflow Categories**: http://localhost:8080/api/workflows/categories

##### Enhanced UI Endpoints
- **Main Dashboard**: http://localhost:3000/dashboard.html
- **Welcome Page**: http://localhost:3000/enhanced-dashboard.html
- **System Redirect**: http://localhost:8080/ → http://localhost:3000

#### NetBox API
- Swagger UI: http://localhost:8000/api/docs/
- API Root: http://localhost:8000/api/

#### Orchestrator API
- GraphQL Playground: http://localhost:8080/api/graphql
- API Documentation: http://localhost:8080/api/docs

## 🧪 Testing

### Unit Tests
```bash
# NetBox tests
cd netbox
python manage.py test

# Orchestrator tests
cd example-orchestrator
python -m pytest tests/
```

### Integration Tests
```bash
# End-to-end workflow tests
python -m pytest tests/integration/

# API tests
python -m pytest tests/api/
```

### Device Type Validation
```bash
# Validate device type definitions
cd devicetype-library
python tests/definitions_test.py
```

## 📈 Performance Optimization

### Database Tuning
- PostgreSQL configuration in `docker-compose.yml`
- Connection pooling enabled
- Optimized queries for large datasets

### Redis Configuration
- Separate Redis instances for NetBox and Orchestrator
- Memory optimization for caching
- Persistence configuration for reliability

### Scaling Considerations
- Horizontal scaling with Docker Swarm or Kubernetes
- Load balancing for multiple orchestrator instances
- Database read replicas for high availability

## 🔒 Security

### Authentication
- NetBox: Token-based API authentication
- Orchestrator: JWT tokens with role-based access
- Database: Encrypted connections and strong passwords

### Network Security
- Container isolation with Docker networks
- Port exposure limited to necessary services
- Environment variable protection for secrets

### Best Practices
- Regular security updates
- Secrets management with Docker secrets or external vaults
- SSL/TLS termination with reverse proxy

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

### Code Standards
- Python: PEP 8 compliance
- Documentation: Docstrings for all functions
- Testing: Minimum 80% code coverage
- Git: Conventional commit messages

### Device Type Contributions
- Follow the device type library schema
- Include comprehensive port definitions
- Add elevation images when possible
- Test with actual hardware when available

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [NetBox](https://github.com/netbox-community/netbox) - Network documentation platform
- [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library) - Community device definitions
- [Workflow Framework](https://github.com/workfloworchestrator/orchestrator-core) - Service orchestration engine

## 📞 Support

### Community Resources
- NetBox Documentation: https://docs.netbox.dev/
- Community Slack: https://netdev.chat/
- GitHub Issues: https://github.com/dashton956-alt/POC/issues

### Getting Help
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and configuration details

---

**Note**: This is a Proof of Concept for demonstration purposes. For production deployment, additional security hardening, monitoring, and backup strategies should be implemented.