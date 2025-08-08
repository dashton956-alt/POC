# Quick Start - Enhanced Web UI Guide

## � Using the Enhanced Orchestrator Dashboard

### Step 1: Access the Enhanced Dashboard
Open your browser and go to: **http://localhost:3000/dashboard.html** ⭐

**Alternative access points:**
- Welcome page: **http://localhost:3000**
- API redirect: **http://localhost:8080** (automatically redirects to UI)

### Step 2: System Overview
The enhanced dashboard provides:
- **🚀 System Status**: Live monitoring of all services with pulse animations
- **📊 NetBox Statistics**: Real-time counts (manufacturers, device types, devices)  
- **⚡ Quick Actions**: One-click access to common operations
- **🗂️ Workflow Categories**: Organized workflow navigation
- **🔄 Auto-refresh**: Statistics update every 30 seconds

### Step 3: Choose Your Workflow Category

**🏭 NetBox Integration** (Recommended for beginners)
- Import device types from community library
- Manage manufacturers and device data
- Synchronize NetBox information

**🔧 Network Operations**  
- L2VPN configuration workflows
- Port management and setup
- Network link configuration

**⚙️ System Management**
- System health checks and monitoring
- Backup and recovery procedures
- Administrative tasks

**🏗️ Infrastructure as Code (IAC)** ⭐ **NEW**
- Automated infrastructure provisioning  
- Configuration management workflows
- Policy-driven infrastructure setup

**🧠 Intent Based Networking** ⭐ **NEW**
- Intelligent network automation
- Intent-based configuration workflows
- Policy-driven network management

### Step 4: Quick Actions (Fastest Way to Start)

**For beginners, use these Quick Actions:**

1. **📦 Import Device Types** 
   - One-click access to device library import
   - Imports manufacturers AND device types
   - Takes 2-5 minutes depending on selection

2. **🌐 Open NetBox DCIM** 
   - Direct link to NetBox interface
   - View imported manufacturers and device types
   - Manage your infrastructure data

3. **💚 System Health Check**
   - Instant system status verification  
   - Shows connectivity to all services
   - Confirms everything is running properly

### Step 5: Monitor Progress with Enhanced Features

The enhanced dashboard shows you:
- ✅ **Real-time Status**: Live indicators with animations
- 📊 **Live Statistics**: Auto-updating counts every 30 seconds
- 🔍 **Visual Feedback**: Loading animations and progress indicators
- ⏱️ **Timestamps**: Last updated information for all data
- 📱 **Mobile Support**: Responsive design for all devices

### Step 6: View Results

After workflow completion:
- **Dashboard Statistics** automatically update with new counts
- **NetBox Integration** shows live data from http://localhost:8000
- **System Status** confirms all services remain healthy
- **Quick Actions** remain available for additional operations

## 🚀 Alternative: Direct Workflow Access

### Traditional Workflow Interface
Access workflows directly at **http://localhost:3000/workflows**:

**Individual Workflow Tasks:**
- **`task_import_vendors`** - Import manufacturers only
- **`task_import_device_types`** - Import device types (requires vendors first)  
- **`task_comprehensive_import`** - Import vendors + device types automatically

### Advanced: GraphQL Playground

For advanced users, use the GraphQL interface at **http://localhost:8080/graphql**:

```graphql
# Start comprehensive import
mutation {
  startWorkflow(input: {workflowName: "task_comprehensive_import"}) {
    workflowId
    status
  }
}

# Check workflow status
query {
  workflow(id: "workflow-id") {
    status
    progress
    result
  }
}
```

## 📊 Enhanced Dashboard Features

### Real-time Monitoring
- **Live Statistics**: NetBox data updates automatically
- **Status Indicators**: Animated pulse effects for active services  
- **Auto-refresh**: 30-second automatic updates
- **Error Handling**: Graceful fallbacks with informative messages

### Professional Interface
- **Modern Design**: Professional CSS with smooth animations
- **Responsive Layout**: Mobile-friendly responsive design
- **Quick Actions**: One-click access to common operations
- **Organized Navigation**: Workflow categories for easy browsing

### System Integration  
- **NetBox Integration**: Direct connection to DCIM data
- **API Integration**: Enhanced backend APIs for dashboard
- **Health Monitoring**: Comprehensive system status checks
- **Workflow Management**: Streamlined workflow organization

## 🎯 Best Practices

### Getting Started Efficiently
1. **Use the Enhanced Dashboard** as your starting point
2. **Check System Status** before running workflows
3. **Start with Quick Actions** for common tasks
4. **Monitor Progress** with real-time updates
5. **Verify Results** in both dashboard and NetBox

### Workflow Selection
- **Beginners**: Use Quick Actions → "Import Device Types"  
- **Advanced Users**: Navigate to specific workflow categories
- **Developers**: Use GraphQL playground for programmatic access
- **System Admins**: Monitor via dashboard health checks

---

**💡 Pro Tip**: The Enhanced Dashboard at http://localhost:3000/dashboard.html provides the most comprehensive overview of your Intent Based Orchestrator system!
mutation {
  startWorkflow(name: "task_comprehensive_import") {
    id
    status
  }
}
```

## 🆘 Troubleshooting

**If the UI doesn't work:**
1. Check services are running: `make health`
2. Restart services if needed: `make restart`
3. Check logs: `make logs`

**If imports fail:**
1. Check NetBox API token is configured
2. Ensure devicetype-library is available
3. View detailed error messages in the UI

## 📋 Available Workflows

| Workflow Name | Description | Duration | Safety |
|---------------|-------------|----------|---------|
| `task_import_vendors` | Import vendors/manufacturers | ~1 min | Very Safe |
| `task_import_device_types` | Import device types (limited to 50) | ~5-10 min | Safe |
| `task_comprehensive_import` | Import vendors + device types | ~10-15 min | Safe |
| `task_bootstrap_netbox` | Create initial NetBox objects | ~1 min | Safe |
| `task_wipe_netbox` | Clean NetBox data | ~1 min | ⚠️ Destructive |

## 💡 Tips

- Start with `task_import_vendors` first if you're new
- Use `task_comprehensive_import` for complete setup
- The UI provides much better feedback than command line scripts
- You can safely run imports multiple times (duplicates are skipped)
- Check NetBox at http://localhost:8000 to see imported data
