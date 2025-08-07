# NetBox Import Guide

This guide explains how to import vendors and device types from the devicetype-library into NetBox using both standalone scripts and orchestrator workflows.

## Quick Start - Using the Web UI

**The easiest way to run imports is through the Orchestrator Web UI:**

1. **Access the UI**: http://localhost:3000
2. **Navigate to Workflows** section  
3. **Select a task**:
   - `task_import_vendors` - Import all vendors/manufacturers
   - `task_import_device_types` - Import device types (limited for safety)
   - `task_comprehensive_import` - Import everything (vendors first, then device types)
4. **Click "Start Workflow"**
5. **Monitor progress** in real-time with detailed step-by-step feedback

**Alternative**: Use GraphQL Playground at http://localhost:8080/graphql for more advanced control.

## Overview

The project provides multiple ways to import data from the devicetype-library:

1. **Standalone Scripts** - Direct Python scripts for immediate imports
2. **Orchestrator Workflows** - Integrated workflows for coordinated imports
3. **Makefile Commands** - Simplified commands for common operations

## Standalone Scripts

### Vendor Import (`vendor_import.py`)

Import manufacturers/vendors from devicetype-library into NetBox.

```bash
# Import all vendors
python3 vendor_import.py

# Import specific vendor
python3 vendor_import.py --vendor cisco

# List available vendors
python3 vendor_import.py --list

# Show statistics
python3 vendor_import.py --stats

# Dry run (show what would be imported)
python3 vendor_import.py --dry-run
```

### Device Type Import (`device_type_import.py`)

Import device types from devicetype-library into NetBox.

```bash
# Import device types (limited to 50 for safety)
python3 device_type_import.py --limit 50

# Import all device types for a specific vendor
python3 device_type_import.py --vendor Cisco

# List available device types
python3 device_type_import.py --list

# Show statistics
python3 device_type_import.py --stats

# Dry run (show what would be imported)
python3 device_type_import.py --dry-run --limit 10
```

## Makefile Commands

Simplified commands using the Makefile:

```bash
# Vendor operations
make import-vendors           # Import all vendors
make import-vendors-dry       # Dry run vendor import
make import-vendors-stats     # Show vendor statistics
make list-vendors            # List available vendors

# Device type operations
make import-device-types      # Import device types (limited to 50)
make import-device-types-dry  # Dry run device type import
make import-device-types-cisco # Import only Cisco device types
make import-device-types-stats # Show device type statistics
make list-device-types       # List available device types

# Combined operations
make import-all-devicetypes   # Import vendors + device types (vendors first)

# View help
make help                    # Show all available commands
```

## Orchestrator Workflows

The import functionality is integrated into the orchestrator as workflow tasks:

### Available Workflow Tasks

1. **`task_import_vendors`** - Import vendors from devicetype-library
2. **`task_import_device_types`** - Import device types from devicetype-library
3. **`task_comprehensive_import`** - Import both vendors and device types in correct order
4. **`task_bootstrap_netbox`** - Create initial NetBox objects (existing)
5. **`task_wipe_netbox`** - Clean NetBox data (existing)

### Running Workflows

#### Via Orchestrator API

```bash
# Import vendors
curl -X POST http://localhost:8080/api/workflows/task_import_vendors

# Import device types
curl -X POST http://localhost:8080/api/workflows/task_import_device_types

# Comprehensive import (vendors + device types)
curl -X POST http://localhost:8080/api/workflows/task_comprehensive_import
```

#### Via Web UI

**Orchestrator UI (Recommended):**

1. Open http://localhost:3000 in your browser
2. Navigate to "Workflows" section
3. Look for available task workflows:
   - `task_import_vendors`
   - `task_import_device_types` 
   - `task_comprehensive_import`
   - `task_bootstrap_netbox`
   - `task_wipe_netbox`
4. Click "Start Workflow" button for the desired task
5. Monitor progress in real-time through the UI

**GraphQL Playground:**

1. Open http://localhost:8080/graphql in your browser
2. Use the GraphQL playground interface
3. Run workflow mutations:

```graphql
# Start vendor import
mutation {
  startWorkflow(name: "task_import_vendors") {
    id
    status
  }
}

# Start device type import
mutation {
  startWorkflow(name: "task_import_device_types") {
    id
    status
  }
}

# Start comprehensive import (vendors + device types)
mutation {
  startWorkflow(name: "task_comprehensive_import") {
    id
    status
  }
}

# Query workflow status
query {
  workflow(id: "workflow-id-here") {
    id
    status
    steps {
      name
      status
      result
    }
  }
}
```

#### List Available Workflows

```bash
make list-workflows          # Show all available workflows
python3 list_workflows.py    # Direct script execution
```

### Monitoring Workflows

#### Via Orchestrator UI

1. **Workflow Dashboard**: http://localhost:3000
   - Real-time workflow status
   - Step-by-step progress tracking
   - Error details and logs
   - Historical workflow runs

2. **Workflow Details**:
   - Click on any running/completed workflow
   - View individual step status
   - See step results and data
   - Monitor execution time

#### Via API/GraphQL

```bash
# Get workflow status via API
curl http://localhost:8080/api/workflows/{workflow-id}

# Monitor logs
make logs-orchestrator
```

#### Via Terminal Logs

```bash
# Real-time orchestrator logs
make logs-orchestrator

# NetBox logs (for import results)
make logs-netbox
```

## User Interface Access

### Orchestrator Web UI

**URL**: http://localhost:3000

**Features**:
- Visual workflow dashboard
- Real-time progress tracking
- Step-by-step execution details
- Error handling and retry options
- Historical workflow runs
- Interactive workflow management

**How to Use**:
1. Open http://localhost:3000 in your browser
2. Look for "Workflows" or "Tasks" section
3. Find import-related workflows:
   - `task_import_vendors`
   - `task_import_device_types`
   - `task_comprehensive_import`
4. Click "Start" or "Execute" button
5. Monitor progress with live updates

### GraphQL Playground

**URL**: http://localhost:8080/graphql

**Features**:
- Interactive query/mutation interface
- Schema exploration
- Advanced workflow control
- Direct API access

**Benefits of UI vs Scripts**:
- ✅ Real-time progress monitoring
- ✅ Visual step-by-step feedback
- ✅ No command line required
- ✅ Error details in web interface  
- ✅ Workflow history and logs
- ✅ Retry failed workflows easily

## Configuration

### Environment Variables

Set these environment variables or create a `.env` file:

```bash
NETBOX_URL=http://localhost:8000
NETBOX_TOKEN=your-netbox-api-token
```

### NetBox API Token

1. Log into NetBox at http://localhost:8000
2. Go to Admin → API → Tokens
3. Create a new token with read/write permissions
4. Use this token in your environment

## Import Process Flow

### Recommended Import Order

1. **Import Vendors First** - Device types require manufacturers to exist
2. **Import Device Types** - Reference the imported manufacturers

```bash
# Recommended sequence
make import-vendors           # Import all vendors/manufacturers
make import-device-types      # Import device types (they'll reference vendors)

# Or use the combined command
make import-all-devicetypes   # Does both in correct order
```

### Workflow Process

The orchestrator workflows follow this pattern:

1. **Analysis Step** - Scan devicetype-library for available data
2. **Import Step** - Create objects in NetBox with error handling
3. **Summary Step** - Report results and statistics

## Safety Features

### Duplicate Prevention

- Scripts check for existing vendors/device types before importing
- Existing items are skipped, not overwritten
- Import statistics show skipped vs. imported counts

### Limits and Controls

- Device type imports are limited by default (50 items)
- Use `--limit` parameter to control import size
- Dry run options show what would be imported without making changes

### Error Handling

- Failed imports are logged with detailed error messages
- Partial failures don't stop the entire import process
- Import summaries show success/failure statistics

## Troubleshooting

### Common Issues

1. **Connection Errors**
   ```bash
   # Check NetBox is running
   make health
   
   # Check NetBox logs
   make logs-netbox
   ```

2. **Authentication Errors**
   ```bash
   # Verify API token
   curl -H "Authorization: Token your-token" http://localhost:8000/api/
   ```

3. **Devicetype Library Missing**
   ```bash
   # Ensure devicetype-library is cloned
   git submodule update --init --recursive
   ```

### Debugging

```bash
# View detailed logs during import
make logs-orchestrator  # Orchestrator logs

# Check import results in NetBox UI
# http://localhost:8000/dcim/manufacturers/
# http://localhost:8000/dcim/device-types/
```

## Examples

### Basic Import Workflow

```bash
# 1. Check what's available
make list-vendors
make import-vendors-stats

# 2. Import vendors
make import-vendors

# 3. Import device types (limited)
make import-device-types

# 4. Check results
make import-vendors-stats
make import-device-types-stats
```

### Selective Import

```bash
# Import only Cisco vendors and device types
python3 vendor_import.py --vendor Cisco
python3 device_type_import.py --vendor Cisco

# Or test first with dry run
python3 device_type_import.py --vendor Cisco --dry-run
```

### Using Orchestrator

```bash
# Start orchestrator workflows via API
curl -X POST http://localhost:8080/api/workflows/task_comprehensive_import

# Monitor via logs
make logs-orchestrator
```

## Performance Notes

- Vendor imports are typically fast (< 1 minute for all vendors)
- Device type imports take longer due to YAML parsing and validation
- Use `--limit` parameter for device types to control import size
- Comprehensive imports may take 10-30 minutes for large datasets

## Data Sources

The devicetype-library contains:
- 100+ vendor directories
- 1000+ device type definitions
- Standardized YAML format with device specifications
- Community-maintained and regularly updated
