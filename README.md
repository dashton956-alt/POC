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

4. **Import Device Types**
   ```bash
   python device_import.py
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

### 2. Orchestrator Workflows

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