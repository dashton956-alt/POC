# Enhanced Dashboard User Guide

## 🎨 Intent Based Orchestrator - Enhanced Dashboard

The Intent Based Orchestrator now features a modern, professional web dashboard that provides comprehensive system monitoring, NetBox integration, and streamlined workflow management.

## 🚀 Quick Access

### Primary Interface
- **Enhanced Dashboard**: http://localhost:3000/dashboard.html
- **Welcome Page**: http://localhost:3000
- **NetBox DCIM**: http://localhost:8000  
- **API Documentation**: http://localhost:8080/api/docs

### Quick Navigation
```bash
# Direct dashboard access
open http://localhost:3000/dashboard.html

# Welcome landing page
open http://localhost:3000/enhanced-dashboard.html

# API redirect (automatically goes to UI)
open http://localhost:8080/
```

## 📊 Dashboard Overview

### System Status Section
Monitor all critical services with real-time status indicators:
- **Intent Based Orchestrator**: API engine status (port 8080)
- **NetBox DCIM**: Data center infrastructure management (port 8000)  
- **Orchestrator UI**: Current web interface status (port 3000)

**Features:**
- 🟢 Live pulse animations for running services
- 🔴 Error indicators for offline services
- ⚡ Quick action buttons for each service
- 🔄 Manual refresh capability

### NetBox Statistics Card
Real-time statistics from your NetBox DCIM system:
- **Manufacturers**: Total number of device manufacturers
- **Device Types**: Complete device type library count
- **Devices**: Active devices in your infrastructure

**Features:**
- 📈 Auto-refresh every 30 seconds
- 🔄 Manual refresh button
- ⏰ Last updated timestamp
- 📊 Hover effects for interactive experience

### Quick Actions Section
One-click access to common operations:
- **Import Device Types**: Access device library import workflow
- **Open NetBox DCIM**: Direct link to NetBox interface
- **API Documentation**: Comprehensive API reference
- **System Health Check**: Instant system status popup

## 🗂️ Workflow Categories

### 1. NetBox Integration 🏭
**Purpose**: Device and manufacturer management
- Device types import from community library
- Manufacturer data synchronization
- NetBox data management

### 2. Network Operations 🔧
**Purpose**: Network configuration and management  
- L2VPN configuration workflows
- Port management and configuration
- Network link setup and management

### 3. System Management ⚙️
**Purpose**: System administration and monitoring
- Comprehensive system health checks
- Backup and recovery procedures
- Administrative tasks and maintenance

### 4. Infrastructure as Code (IAC) 🏗️ **NEW**
**Purpose**: Automated infrastructure provisioning
- Infrastructure automation workflows
- Configuration management
- Policy-driven provisioning

### 5. Intent Based Networking 🧠 **NEW**
**Purpose**: Intelligent network automation
- Intent-based configuration workflows
- Intelligent network automation
- Policy-driven network management

## 🎨 Design Features

### Professional Styling
- **Modern CSS**: CSS Grid layouts with flexbox components
- **Responsive Design**: Mobile-friendly responsive breakpoints
- **Professional Colors**: Consistent color scheme with CSS variables
- **Smooth Animations**: Hover effects, pulse animations, loading indicators

### User Experience
- **Auto-refresh**: Statistics update automatically every 30 seconds
- **Visual Feedback**: Loading indicators and status animations
- **Error Handling**: Graceful fallbacks with informative messages
- **Navigation**: Intuitive workflow organization and quick actions

### Technical Features
- **ES6+ JavaScript**: Modern JavaScript with async/await
- **Fetch API**: RESTful API integration with error handling
- **CSS Variables**: Maintainable theming system
- **Mobile Responsive**: Optimized for all device sizes

## 🔧 Advanced Usage

### API Integration
The dashboard integrates with enhanced backend APIs:

```javascript
// Get NetBox statistics
const stats = await fetch('/api/dashboard/netbox-stats').then(r => r.json());

// Get system status  
const status = await fetch('/api/dashboard/system-status').then(r => r.json());

// Search devices
const results = await fetch('/api/netbox/search?q=cisco').then(r => r.json());
```

### Workflow Navigation
All workflow categories link to the orchestrator's workflow system:
- Organized by functional area
- Direct integration with workflow engine
- Real-time status and progress monitoring

### System Health Monitoring
Built-in health check functionality:
- **System Health Check**: Quick status verification popup
- **Auto-refresh**: Continuous monitoring with 30-second intervals
- **Visual Indicators**: Animated pulse for active services
- **Error Detection**: Automatic fallback to sample data on API failures

## 🛠️ Configuration

### Docker Integration
The enhanced UI is integrated via Docker volume mounts:
```yaml
volumes:
  - ./docker/orchestrator-ui/public/dashboard.html:/app/public/dashboard.html
  - ./docker/orchestrator-ui/public/index.html:/app/public/enhanced-dashboard.html
```

### API Endpoints
Enhanced backend provides dashboard-specific APIs:
- `/api/dashboard/netbox-stats` - Real-time NetBox statistics
- `/api/dashboard/system-status` - System health information  
- `/api/workflows/categories` - Organized workflow categories
- `/api/netbox/search` - NetBox device search with filtering

### Environment Variables
Configure the enhanced UI through environment variables:
```bash
ENVIRONMENT_NAME="Intent Based Orchestrator"
SHOW_NETBOX_STATUS=true
NETBOX_URL=http://localhost:8000
DASHBOARD_QUICK_ACTIONS=true
WORKFLOW_CATEGORIES_ENABLED=true
```

## 🔍 Troubleshooting

### Dashboard Not Loading
```bash
# Check orchestrator-ui container
docker ps | grep orchestrator-ui

# Check volume mounts
docker inspect orchestrator-ui | grep Mounts -A 10

# Verify file exists
ls -la docker/orchestrator-ui/public/dashboard.html
```

### Statistics Not Updating
```bash
# Test API endpoints
curl http://localhost:8080/api/dashboard/netbox-stats

# Check browser console for JavaScript errors
# Verify NetBox connectivity
curl http://localhost:8000/api/status/
```

### Workflow Navigation Issues
```bash
# Test workflow categories API
curl http://localhost:8080/api/workflows/categories

# Check orchestrator API health
curl http://localhost:8080/api/system-status
```

## 📱 Mobile Experience

### Responsive Breakpoints
- **Desktop**: Full grid layout with all features
- **Tablet**: Adapted grid with optimized spacing
- **Mobile**: Single column layout with touch-friendly interactions

### Mobile Features
- Touch-optimized action buttons
- Collapsible navigation menu
- Optimized text sizes and spacing
- Smooth scroll navigation

## 🚀 Getting Started

### For New Users
1. **Start Services**: `docker-compose up -d`
2. **Access Dashboard**: http://localhost:3000/dashboard.html
3. **Check System Status**: Verify all services show green indicators
4. **Import Data**: Use "Import Device Types" quick action
5. **Explore Workflows**: Browse workflow categories

### For Developers
1. **API Documentation**: http://localhost:8080/api/docs
2. **GraphQL Playground**: http://localhost:8080/graphql  
3. **Dashboard APIs**: Test enhanced endpoints
4. **Custom Workflows**: Create new workflow categories
5. **UI Customization**: Modify dashboard styling and functionality

---

**💡 Pro Tip**: Bookmark http://localhost:3000/dashboard.html for quick access to your complete system overview!
