# Quick Start - Web UI Guide

## 🌐 Using the Orchestrator Web Interface

### Step 1: Access the UI
Open your browser and go to: **http://localhost:3000**

### Step 2: Navigate to Workflows
Look for the "Workflows" section in the navigation menu.

### Step 3: Choose an Import Task

**For beginners, we recommend starting with:**

1. **`task_import_vendors`** 
   - Imports all manufacturers/vendors from devicetype-library
   - Safe and quick (usually completes in under 1 minute)
   - Required before importing device types

2. **`task_comprehensive_import`** 
   - Imports both vendors AND device types in correct order
   - Takes longer but does everything automatically
   - Best for complete setup

### Step 4: Start the Workflow
1. Click on your chosen workflow
2. Click "Start Workflow" or "Execute" button
3. Watch the real-time progress

### Step 5: Monitor Progress
The UI will show you:
- ✅ Each step as it completes
- 📊 Import statistics (how many items imported/skipped/failed)
- 🔍 Detailed logs and error messages
- ⏱️ Execution time

### Step 6: View Results
After completion:
- Check the workflow summary for statistics
- Visit NetBox at http://localhost:8000 to see imported data
- Go to "Organization" → "Manufacturers" to see imported vendors
- Go to "Devices" → "Device Types" to see imported device types

## 🚀 Alternative: GraphQL Playground

For advanced users, use the GraphQL interface at **http://localhost:8080/graphql**:

```graphql
# Start comprehensive import
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
