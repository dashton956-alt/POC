# API Documentation - Enhanced Dashboard

## 🔌 Intent Based Orchestrator API Reference

The Intent Based Orchestrator provides comprehensive API endpoints for dashboard functionality, NetBox integration, and system monitoring.

## 📊 Dashboard APIs

### Get NetBox Statistics
**Endpoint:** `GET /api/dashboard/netbox-stats`

Returns real-time statistics from NetBox DCIM system.

**Response:**
```json
{
  "manufacturers": 15,
  "device_types": 342,
  "devices": 127,
  "last_updated": "2025-08-08T10:30:45.123Z"
}
```

**Error Handling:**
- Returns sample data if NetBox is unavailable
- Graceful degradation with informative error messages

### Get System Status
**Endpoint:** `GET /api/dashboard/system-status`

Returns comprehensive system health information.

**Response:**
```json
{
  "orchestrator": {
    "status": "running",
    "url": "http://localhost:8080"
  },
  "netbox": {
    "status": "running", 
    "url": "http://localhost:8000"
  },
  "ui": {
    "status": "running",
    "url": "http://localhost:3000"
  },
  "last_updated": "2025-08-08T10:30:45.123Z"
}
```

### Get Dashboard Statistics
**Endpoint:** `GET /api/dashboard/statistics`

Returns comprehensive dashboard data including NetBox integration status.

**Response:**
```json
{
  "netbox_status": "connected",
  "total_manufacturers": 15,
  "total_device_types": 342,
  "total_devices": 127,
  "recent_imports": [],
  "popular_manufacturers": [
    {"name": "Cisco", "slug": "cisco"},
    {"name": "Juniper", "slug": "juniper"}
  ],
  "last_updated": "2025-08-08T10:30:45.123Z"
}
```

### Get Import Status
**Endpoint:** `GET /api/dashboard/import-status`

Returns current import workflow status and progress.

**Response:**
```json
{
  "active_imports": [],
  "completed_imports": [],
  "failed_imports": [],
  "import_queue_size": 0
}
```

## 🏭 NetBox Integration APIs

### Get Manufacturer Summary
**Endpoint:** `GET /api/netbox/manufacturers`

Returns detailed manufacturer information with device counts.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Cisco",
    "slug": "cisco",
    "device_count": 89,
    "description": "Cisco Systems, Inc.",
    "url": "https://cisco.com"
  }
]
```

### Search NetBox Devices
**Endpoint:** `GET /api/netbox/search`

Advanced device search with filtering capabilities.

**Parameters:**
- `q` (string): Search query
- `manufacturer` (string): Filter by manufacturer
- `limit` (integer): Limit results (default: 50)

**Example Request:**
```
GET /api/netbox/search?q=catalyst&manufacturer=cisco&limit=10
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "model": "Catalyst 9300-48P",
      "manufacturer": "Cisco",
      "slug": "catalyst-9300-48p",
      "part_number": "C9300-48P",
      "u_height": 1
    }
  ],
  "count": 1
}
```

## 🗂️ Workflow Management APIs

### Get Workflow Categories
**Endpoint:** `GET /api/workflows/categories`

Returns organized workflow categories for navigation.

**Response:**
```json
{
  "NetBox Integration": {
    "description": "Device and manufacturer import workflows",
    "workflows": [
      {
        "name": "Import Device Types",
        "path": "/workflows/device-types",
        "description": "Import device types from library"
      }
    ]
  },
  "Network Operations": {
    "description": "Network configuration and management",
    "workflows": [
      {
        "name": "Configure L2VPN", 
        "path": "/workflows/l2vpn",
        "description": "Layer 2 VPN configuration"
      }
    ]
  },
  "System Management": {
    "description": "System administration and monitoring",
    "workflows": [
      {
        "name": "System Health Check",
        "path": "/workflows/health", 
        "description": "Check system health"
      }
    ]
  },
  "Infrastructure as Code (IAC)": {
    "description": "Automated infrastructure provisioning",
    "workflows": [
      {
        "name": "Provision Infrastructure",
        "path": "/workflows/iac-provision",
        "description": "Automated infrastructure setup"
      }
    ]
  },
  "Intent Based Networking": {
    "description": "Intelligent network automation",
    "workflows": [
      {
        "name": "Intent Configuration",
        "path": "/workflows/intent-config",
        "description": "Policy-driven network setup"
      }
    ]
  }
}
```

## 📚 Help and Documentation APIs

### Get NetBox Integration Help
**Endpoint:** `GET /api/help/netbox-integration`

Returns comprehensive help content for NetBox integration.

**Response:**
```json
{
  "title": "NetBox Integration Guide",
  "sections": [
    {
      "title": "Getting Started",
      "content": "The Intent Based Orchestrator integrates seamlessly with NetBox DCIM..."
    },
    {
      "title": "Device Import Process",
      "content": "Import device types from the community device-type library...",
      "steps": [
        "Navigate to Workflows > NetBox Integration",
        "Select 'Import Device Types' workflow",
        "Choose manufacturers to import"
      ]
    }
  ]
}
```

## 🌐 UI Redirect Endpoints

### Dashboard Redirect
**Endpoint:** `GET /dashboard`

Redirects to the enhanced dashboard on UI port.

**Response:** `302 Redirect` → `http://localhost:3000/dashboard.html`

### System Status Redirect  
**Endpoint:** `GET /status`

Redirects to the enhanced dashboard for system status viewing.

**Response:** `302 Redirect` → `http://localhost:3000/dashboard.html`

### Root Redirect
**Endpoint:** `GET /`

Redirects root API access to the main UI.

**Response:** `302 Redirect` → `http://localhost:3000`

## 🔧 Legacy System APIs

### System Status (Legacy)
**Endpoint:** `GET /api/system-status`

Legacy system status endpoint for backward compatibility.

**Response:**
```json
{
  "orchestrator": "running",
  "netbox_connection": "connected",
  "database": "healthy",
  "redis": "connected"
}
```

## 🛠️ Usage Examples

### JavaScript (Dashboard Integration)
```javascript
// Get NetBox statistics
async function getNetBoxStats() {
  try {
    const response = await fetch('/api/dashboard/netbox-stats');
    const stats = await response.json();
    
    document.getElementById('manufacturers-count').textContent = stats.manufacturers;
    document.getElementById('device-types-count').textContent = stats.device_types;
    document.getElementById('devices-count').textContent = stats.devices;
  } catch (error) {
    console.error('Failed to fetch NetBox stats:', error);
  }
}

// Search devices
async function searchDevices(query) {
  const response = await fetch(`/api/netbox/search?q=${encodeURIComponent(query)}`);
  return await response.json();
}
```

### Python (Script Integration)
```python
import requests

# Get dashboard statistics
def get_dashboard_stats():
    response = requests.get('http://localhost:8080/api/dashboard/statistics')
    return response.json()

# Search NetBox devices
def search_devices(query, manufacturer=None):
    params = {'q': query}
    if manufacturer:
        params['manufacturer'] = manufacturer
    
    response = requests.get(
        'http://localhost:8080/api/netbox/search',
        params=params
    )
    return response.json()
```

### cURL (Command Line)
```bash
# Get system status
curl http://localhost:8080/api/dashboard/system-status

# Get NetBox statistics  
curl http://localhost:8080/api/dashboard/netbox-stats

# Search for Cisco devices
curl "http://localhost:8080/api/netbox/search?q=catalyst&manufacturer=cisco"

# Get workflow categories
curl http://localhost:8080/api/workflows/categories
```

## ⚡ Rate Limiting and Performance

### Dashboard APIs
- **Auto-refresh**: Optimized for 30-second intervals
- **Caching**: Intelligent caching for frequently accessed data
- **Error Handling**: Graceful degradation with fallback data

### NetBox Integration
- **Connection Pooling**: Optimized NetBox API connections
- **Timeout Handling**: 10-second timeout for external API calls
- **Retry Logic**: Built-in retry for transient failures

### Search APIs
- **Result Limiting**: Default 50 results, configurable
- **Query Optimization**: Efficient NetBox API usage
- **Response Caching**: Temporary caching for identical queries

## 🔒 Authentication and Security

### API Authentication
- **Internal APIs**: Container-to-container communication (no auth required)
- **External NetBox**: Token-based authentication configured via environment
- **CORS**: Properly configured for dashboard integration

### Security Headers
- **Content-Type**: Enforced JSON content type
- **Error Sanitization**: Safe error messages without sensitive data
- **Input Validation**: Proper query parameter validation

---

**💡 Pro Tip**: All dashboard APIs are optimized for real-time updates and provide graceful fallbacks for offline scenarios!
