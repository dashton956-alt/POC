# NetBox Orchestrator POC

A comprehensive Proof of Concept (POC) demonstrating Intent-Based Networking (IBN) using NetBox for network documentation and orchestration capabilities. This project combines NetBox with a custom orchestrator to provide automated network device management, configuration, and monitoring.

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

2. **Start NetBox Services**
   ```bash
   cd netbox
   docker-compose up -d
   ```

3. **Start Orchestrator Services**
   ```bash
   cd ../example-orchestrator
   docker-compose up -d
   ```

4. **Import Data from Devicetype Library**
   
   **Option A: Web UI (Recommended)**
   ```bash
   # Open http://localhost:3000 in your browser
   # Navigate to "Workflows" and run:
   # - import_vendors (multi-vendor selection with direct NetBox integration)
   ```
   
   **Option B: Command Line**
   ```bash
   make import-all-devicetypes    # Import vendors + device types
   # OR use individual scripts:
   python3 vendor_import.py       # Import vendors/manufacturers
   python3 device_type_import.py --limit 50  # Import device types
   ```

5. **Access the Applications**
   - NetBox: http://localhost:8000
   - Orchestrator UI: http://localhost:3000
   - Orchestrator API: http://localhost:8080

## 📋 Project Structure

```
POC/
├── netbox/                     # NetBox IPAM/DCIM platform
│   ├── docker-compose.yml     # NetBox container orchestration
│   ├── configuration/         # NetBox configuration files
│   ├── docker/                # Docker build files
│   ├── test-configuration/    # Test environment configs
│   └── ...
├── example-orchestrator/       # Custom orchestrator service
│   ├── docker-compose.yml     # Orchestrator container setup
│   ├── workflows/             # Automation workflows & tasks
│   │   └── tasks/             # Individual workflow tasks
│   ├── products/              # Product definitions
│   ├── services/              # Integration services
│   ├── ansible/               # Ansible playbooks
│   ├── clab/                  # Container Lab configs
│   ├── migrations/            # Database migrations
│   ├── templates/             # Jinja2 templates
│   ├── translations/          # Internationalization
│   └── utils/                 # Utility functions
├── devicetype-library/         # NetBox device type definitions
│   ├── device-types/          # Device type YAML files (8000+)
│   ├── module-types/          # Module type definitions
│   ├── elevation-images/      # Device elevation images
│   ├── module-images/         # Module images
│   ├── schema/                # Validation schemas
│   ├── scripts/               # Utility scripts
│   └── tests/                 # Test suites
├── docs/                      # 📚 Comprehensive Documentation
│   ├── README.md              # Documentation index
│   ├── HIGH_LEVEL_DESIGN.md   # System architecture overview
│   ├── LOW_LEVEL_DESIGN.md    # Technical implementation details
│   └── diagrams/              # System diagrams (Mermaid format)
│       ├── 01_system_architecture_level1.md
│       ├── 02_component_architecture_level2.md
│       ├── 03_vendor_import_workflow.md
│       ├── 04_data_flow_integration.md
│       ├── 05_sequence_diagram_workflow.md
│       └── 06_product_roadmap_kanban.md
├── .env.example               # Environment configuration template
├── docker-compose.dev.yml     # Development environment setup
├── Makefile                   # Build and deployment commands
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
├── IMPORT_GUIDE.md            # Device import instructions
├── UI_QUICKSTART.md           # Quick start for UI
├── quickstart.sh              # Automated setup script
└── README.md                  # This file
```

## 🛠️ Components

### NetBox
- **Purpose**: Network documentation and IPAM
- **Port**: 8000
- **Features**: Device inventory, IP management, circuit tracking
- **Database**: PostgreSQL
- **Cache**: Redis (port 6379)

### Orchestrator
- **Purpose**: Workflow automation and service orchestration
- **Port**: 8080 (API), 3000 (UI)
- **Features**: GraphQL API, workflow engine, NetBox integration
- **Database**: PostgreSQL
- **Cache**: Redis (port 6380)

### Device Type Library
- **Purpose**: Standardized device definitions
- **Content**: 8000+ device types from major vendors
- **Format**: YAML with JSON schema validation
- **Vendors**: Cisco, Juniper, Arista, HP, Dell, and many more

### Documentation System
- **Purpose**: Comprehensive system documentation
- **Location**: `/docs` directory
- **Formats**: Markdown with Mermaid diagrams
- **Content**: Architecture designs, technical specifications, project roadmap
- **Access**: Native GitHub rendering, no external dependencies

## 📚 Documentation

This project includes comprehensive documentation covering all aspects of the system:

### 🎯 Quick Access
- **[Documentation Hub](docs/README.md)** - Complete documentation index
- **[High-Level Design](docs/HIGH_LEVEL_DESIGN.md)** - System architecture and business logic
- **[Low-Level Design](docs/LOW_LEVEL_DESIGN.md)** - Technical implementation details

### 📊 System Diagrams
All diagrams use Mermaid format for native GitHub rendering:
- **[System Architecture](docs/diagrams/01_system_architecture_level1.md)** - High-level system overview
- **[Component Architecture](docs/diagrams/02_component_architecture_level2.md)** - Detailed component interactions
- **[Vendor Import Workflow](docs/diagrams/03_vendor_import_workflow.md)** - Complete workflow process
- **[Data Flow Integration](docs/diagrams/04_data_flow_integration.md)** - Data processing pipeline
- **[Sequence Diagram](docs/diagrams/05_sequence_diagram_workflow.md)** - Execution timeline
- **[Product Roadmap](docs/diagrams/06_product_roadmap_kanban.md)** - Development milestones

## 🆕 Recent Updates

### Version 2.0 Features
- ✅ **Multi-Vendor Selection**: Choose specific vendors or select all for import
- ✅ **Enhanced Workflow Engine**: Improved state management and error handling
- ✅ **Direct NetBox Integration**: Streamlined vendor import without dry-run mode
- ✅ **Comprehensive Documentation**: Complete system design and technical specifications
- ✅ **Mermaid Diagrams**: Native GitHub-rendered diagrams (no external dependencies)
- ✅ **Improved Error Handling**: Detailed logging and graceful failure recovery

### Workflow Enhancements
- **Unlimited Vendor Selection**: No restrictions on number of vendors to import
- **Real-time Progress Tracking**: Monitor workflow execution status
- **Comprehensive Logging**: Detailed audit trail for all operations
- **Automatic Recovery**: Retry mechanisms for failed operations

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

### 1. Vendor Import Workflow (Primary Feature)

#### Web UI Method (Recommended)
```bash
# 1. Open the orchestrator UI
http://localhost:3000

# 2. Navigate to Workflows section
# 3. Select "Import Vendors" workflow
# 4. Choose vendors to import:
#    - Select specific vendors (Cisco, Arista, Juniper, etc.)
#    - Or select "All" for complete import
# 5. Submit workflow and monitor progress
```

#### API Method
```bash
curl -X POST http://localhost:8080/api/workflows/import-vendors \
  -H "Content-Type: application/json" \
  -d '{
    "selected_vendors": ["Cisco", "Arista", "Juniper"],
    "import_all": false
  }'
```

#### Monitor Workflow Status
```bash
curl http://localhost:8080/api/workflows/{workflow_id}/status
```

### 2. NetBox Operations

#### Access NetBox
```bash
# Web Interface
http://localhost:8000

# Default credentials
Username: admin
Password: admin
```

#### Create API Token
1. Login to NetBox web interface
2. Go to Admin → Users → API Tokens
3. Create new token for orchestrator integration

#### Python API Usage
```python
import pynetbox
nb = pynetbox.api('http://localhost:8000', token='your-token')

# List imported manufacturers
manufacturers = nb.dcim.manufacturers.all()
print(f"Imported {len(manufacturers)} manufacturers")

# List imported device types
device_types = nb.dcim.device_types.all()
print(f"Imported {len(device_types)} device types")
```

### 3. Advanced Orchestrator Features

#### Create Custom Workflow
```bash
curl -X POST http://localhost:8080/api/workflows/custom \
  -H "Content-Type: application/json" \
  -d '{
    "name": "provision-datacenter",
    "steps": [
      {"type": "create_site", "params": {"name": "DC01"}},
      {"type": "import_devices", "params": {"vendor": "Cisco"}},
      {"type": "configure_network", "params": {"template": "bgp-config"}}
    ]
  }'
```

#### GraphQL Query Example
```graphql
query {
  workflows {
    id
    name
    status
    created_at
    steps {
      name
      status
      duration
    }
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

### Health Checks

```bash
# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check orchestrator health
curl http://localhost:8080/health

# Check NetBox health
curl http://localhost:8000/api/status/
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

#### Port Conflicts
```bash
# Check port usage
ss -tulpn | grep :8000
ss -tulpn | grep :8080
ss -tulpn | grep :3000
```

### Log Access

```bash
# NetBox logs
docker logs netbox-netbox-1

# Orchestrator logs
docker logs orchestrator

# Redis logs
docker logs redis
```

## 🚀 Development

### Branch Structure

This repository uses a structured branching strategy:

```
main                           # Production-ready code
├── netbox-feature-workflows   # Feature development branch
└── documentation              # Comprehensive documentation branch
```

- **main**: Stable, production-ready code
- **netbox-feature-workflows**: Active development of workflow features
- **documentation**: Complete system documentation with Mermaid diagrams

### Setting Up Development Environment

1. **Clone and Setup**
   ```bash
   git clone https://github.com/dashton956-alt/POC.git
   cd POC
   
   # Switch to development branch
   git checkout netbox-feature-workflows
   ```

2. **Environment Configuration**
   ```bash
   # Copy environment templates
   cp .env.example .env
   cp netbox/.env.example netbox/.env
   cp example-orchestrator/.env.example example-orchestrator/.env
   
   # Edit configuration files as needed
   ```

3. **Development Containers**
   ```bash
   # Start all services in development mode
   docker-compose -f docker-compose.dev.yml up -d
   
   # Or start individually:
   # NetBox development mode
   cd netbox
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

   # Orchestrator development mode
   cd ../example-orchestrator
   docker-compose up -d
   ```

4. **Python Development Setup** (for custom scripts)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

### Development Workflow

```bash
# 1. Create feature branch from development
git checkout netbox-feature-workflows
git pull origin netbox-feature-workflows
git checkout -b feature/your-feature-name

# 2. Make changes and test
# 3. Commit with descriptive messages
git add .
git commit -m "feat: add new workflow capability"

# 4. Push and create PR
git push origin feature/your-feature-name
# Create PR to netbox-feature-workflows branch
```

### Current Capabilities

#### ✅ Implemented Features
- **Multi-Vendor Device Import**: Select specific vendors or import all 8000+ device types
- **NetBox Integration**: Direct creation of manufacturers, device types, and components
- **Workflow Engine**: Asynchronous task processing with state management
- **Error Handling**: Comprehensive logging and graceful failure recovery
- **Web UI**: User-friendly interface for workflow management
- **API Access**: RESTful and GraphQL endpoints
- **Documentation**: Complete system architecture and technical specifications

#### 🚧 In Development
- **Performance Optimization**: Caching and parallel processing improvements
- **Advanced Workflows**: Custom workflow builder and template system
- **Monitoring Dashboard**: Real-time system health and performance metrics

#### 📋 Roadmap
- **Authentication & Authorization**: RBAC and enterprise authentication
- **Multi-tenancy**: Organization isolation and resource management
- **Mobile App**: iOS/Android applications for mobile management
- **Advanced Reporting**: Custom reports and analytics
- **Plugin System**: Third-party integrations and extensions

### Code Structure

#### Orchestrator Components
- **`workflows/`**: Workflow definitions and task implementations
  - `tasks/import_vendors.py`: Multi-vendor import workflow
  - `tasks/state_management.py`: Workflow state handling
- **`services/`**: External service integrations
  - `netbox.py`: NetBox API client and operations
  - `git_client.py`: Git repository management
- **`products/`**: Product and service definitions
- **`utils/`**: Utility functions and helpers

#### NetBox Integration
- **`services/netbox.py`**: NetBox API client and authentication
- **`workflows/tasks/import_vendors.py`**: Vendor import implementation
- **Configuration**: Environment-based NetBox connection setup
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

We welcome contributions to improve the NetBox Orchestrator POC! Please see our [Contributing Guidelines](CONTRIBUTING.md) for detailed information.

### Quick Contribution Steps
1. **Fork the repository** and clone your fork
2. **Create a feature branch** from `netbox-feature-workflows`
   ```bash
   git checkout netbox-feature-workflows
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with appropriate tests
4. **Follow code standards**: Python PEP 8, descriptive commit messages
5. **Update documentation** if adding new features
6. **Submit a pull request** to the `netbox-feature-workflows` branch

### Development Guidelines
- **Code Quality**: Follow Python PEP 8 and include docstrings
- **Testing**: Add unit tests for new functionality
- **Documentation**: Update relevant documentation files
- **Commit Messages**: Use conventional commit format (feat:, fix:, docs:, etc.)

### Areas for Contribution
- 🔧 **Core Features**: Workflow engine improvements
- 📊 **UI/UX**: Frontend enhancements and user experience
- 🧪 **Testing**: Test coverage expansion and automation
- 📚 **Documentation**: Technical writing and tutorials
- 🐛 **Bug Fixes**: Issue resolution and stability improvements

## 📞 Support & Community

### Getting Help
- **Documentation**: Start with the [docs/](docs/) directory
- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions and community support

### Resources
- **[High-Level Design](docs/HIGH_LEVEL_DESIGN.md)**: System architecture overview
- **[Low-Level Design](docs/LOW_LEVEL_DESIGN.md)**: Technical implementation details
- **[Import Guide](IMPORT_GUIDE.md)**: Device import procedures
- **[Quick Start Guide](UI_QUICKSTART.md)**: Getting started with the UI
- **[Changelog](CHANGELOG.md)**: Version history and updates

### Project Status
- **Current Version**: 2.0 (Multi-vendor workflow capability)
- **Development Branch**: `netbox-feature-workflows`
- **Documentation Branch**: `documentation`
- **Active Maintenance**: Regular updates and bug fixes
- **Community**: Growing contributor base
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