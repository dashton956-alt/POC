# Low-Level Design: IaC Intent-Based Networking System

## Document Information
- **Document Version**: 1.0
- **Date**: August 7, 2025
- **Author**: Development Team
- **Status**: Draft

---

## 1. Introduction

This document provides detailed technical specifications for the IaC Intent-Based Networking System, covering implementation details, data models, API specifications, and technical architecture decisions.

---

## 2. Technology Stack Details

### 2.1 Backend Stack

#### 2.1.1 Python Framework Stack
```yaml
Core Framework:
  - Python: 3.11+
  - FastAPI: Latest (async web framework)
  - Pydantic: 2.x (data validation and serialization)
  - SQLAlchemy: Latest (ORM and database abstraction)
  - Alembic: Latest (database migrations)

Orchestrator Core:
  - orchestrator-core: 4.0.4 (workflow engine)
  - pydantic-forms: Latest (dynamic form generation)
  - structlog: Latest (structured logging)

Async Processing:
  - AsyncIO: Built-in Python async support
  - Redis: 7+ (message queue and caching)
  - Celery: Future implementation for distributed tasks

API Frameworks:
  - Strawberry GraphQL: Latest (GraphQL implementation)
  - FastAPI: REST API endpoints
  - Uvicorn: ASGI server
```

#### 2.1.2 Database Stack
```yaml
Primary Database:
  - PostgreSQL: 14+
  - Connection Pool: SQLAlchemy pool management
  - Migration Tool: Alembic

Cache Layer:
  - Redis: 7+ (session storage, task queue, caching)
  - Connection: Redis-py async client

Data Validation:
  - Pydantic: Schema validation and serialization
  - Custom validators: Business logic validation
```

### 2.2 Frontend Stack

#### 2.2.1 React Application
```yaml
Core Framework:
  - React: 18+ (component framework)
  - TypeScript: Latest (type safety)
  - Material-UI: Latest (component library)

Build Tools:
  - Vite: Build tool and development server
  - Node.js: 18+ runtime

State Management:
  - React Query: Server state management
  - Context API: Local state management

HTTP Client:
  - Axios: HTTP client for API calls
  - GraphQL: Apollo Client (future implementation)
```

### 2.3 Infrastructure Stack

#### 2.3.1 Containerization
```yaml
Container Runtime:
  - Docker: 24+ (containerization)
  - Docker Compose: Multi-container orchestration

Container Images:
  - orchestrator: Custom Python application
  - orchestrator-ui: Custom React application  
  - postgres: Official PostgreSQL 14
  - redis: Official Redis 7
  - nginx: Official Nginx (reverse proxy)
```

---

## 3. System Architecture Details

### 3.1 Application Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                  │
├─────────────────────────────────────────────────────────┤
│  Web Framework (FastAPI)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   GraphQL   │  │    REST     │  │  WebSocket  │   │
│  │  Endpoints  │  │ Endpoints   │  │   Support   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
├─────────────────────────────────────────────────────────┤
│  Business Logic Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Workflow   │  │   Service   │  │ Validation  │   │
│  │  Handlers   │  │   Layer     │  │   Layer     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
├─────────────────────────────────────────────────────────┤
│  Data Access Layer                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Repository  │  │    ORM      │  │   Cache     │   │
│  │  Pattern    │  │(SQLAlchemy) │  │  Manager    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Component Interaction

#### 3.2.1 Request Flow
1. **HTTP Request** → Nginx Reverse Proxy
2. **Route Resolution** → FastAPI Router
3. **Authentication** → Auth Middleware (future)
4. **Validation** → Pydantic Models
5. **Business Logic** → Service Layer
6. **Data Access** → Repository Layer
7. **Database Operations** → SQLAlchemy ORM
8. **Response Formation** → Pydantic Serialization
9. **HTTP Response** → Client

#### 3.2.2 Workflow Execution Flow
1. **Workflow Creation** → Form Submission
2. **Validation** → Pydantic Form Models
3. **State Initialization** → Workflow Engine
4. **Step Execution** → Sequential/Parallel Processing
5. **State Persistence** → Database Storage
6. **Event Publishing** → Redis Pub/Sub
7. **Result Aggregation** → Final State Storage

---

## 4. Data Models and Schema

### 4.1 Core Database Schema

#### 4.1.1 Workflow Management Tables
```sql
-- Workflow Definitions
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    target VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process Instances (Workflow Executions)
CREATE TABLE processes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    form_data JSONB,
    state JSONB
);

-- Process Steps
CREATE TABLE process_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_id UUID REFERENCES processes(id),
    step_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_id UUID REFERENCES processes(id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255) -- Future: user tracking
);
```

### 4.2 Pydantic Models

#### 4.2.1 Core Workflow Models
```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowDefinition(BaseModel):
    """Workflow definition schema"""
    id: Optional[str] = None
    name: str = Field(..., description="Unique workflow name")
    target: str = Field(..., description="Workflow target system")
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProcessInstance(BaseModel):
    """Process execution instance"""
    id: Optional[str] = None
    workflow_id: str
    status: WorkflowStatus
    form_data: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ProcessStep(BaseModel):
    """Individual workflow step"""
    id: Optional[str] = None
    process_id: str
    step_name: str
    status: WorkflowStatus
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

#### 4.2.2 NetBox Integration Models
```python
class ManufacturerPayload(BaseModel):
    """NetBox manufacturer creation payload"""
    name: str = Field(..., description="Manufacturer name")
    slug: str = Field(..., description="URL-safe slug")
    description: Optional[str] = None

class DeviceTypePayload(BaseModel):
    """NetBox device type creation payload"""
    manufacturer: str = Field(..., description="Manufacturer slug")
    model: str = Field(..., description="Device model")
    slug: str = Field(..., description="URL-safe slug")
    u_height: int = Field(default=1, description="Rack units")
    is_full_depth: bool = Field(default=True)
    part_number: Optional[str] = None
    description: Optional[str] = None

class ImportResult(BaseModel):
    """Generic import operation result"""
    success_count: int = Field(default=0)
    error_count: int = Field(default=0)
    imported_items: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: Optional[float] = None
```

#### 4.2.3 Form Models
```python
from orchestrator.forms import FormPage

class VendorImportForm(FormPage):
    """Multi-select vendor import form"""
    class Config:
        title = "Import Vendors to NetBox"
        description = "Select vendors to import from devicetype-library"
    
    selected_vendors: List[str] = Field(
        default=["all"],
        description="Select vendors to import"
    )

class DeviceTypeImportForm(FormPage):
    """Device type import form"""
    class Config:
        title = "Import Device Types to NetBox"
        description = "Import device types for selected vendors"
    
    selected_vendor: str = Field(..., description="Select vendor")
    device_type_filter: Optional[str] = Field(
        None,
        description="Filter device types (regex pattern)"
    )
```

---

## 5. API Specifications

### 5.1 REST API Endpoints

#### 5.1.1 Workflow Management
```python
# Endpoint: /api/workflows
@router.get("/workflows", response_model=List[WorkflowDefinition])
async def list_workflows():
    """Get all available workflows"""
    pass

@router.post("/workflows/{workflow_name}", response_model=ProcessInstance)
async def start_workflow(
    workflow_name: str,
    form_data: Dict[str, Any] = Body(...)
):
    """Start workflow execution"""
    pass

@router.get("/processes/{process_id}", response_model=ProcessInstance)
async def get_process(process_id: str):
    """Get process execution status"""
    pass

@router.delete("/processes/{process_id}")
async def cancel_process(process_id: str):
    """Cancel running process"""
    pass
```

#### 5.1.2 Health and Status
```python
# Endpoint: /api/health
@router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "netbox": "healthy"
        }
    }
```

### 5.2 GraphQL Schema

#### 5.2.1 Core Types
```graphql
type Workflow {
    id: ID!
    name: String!
    target: String!
    description: String
    createdAt: DateTime!
    updatedAt: DateTime!
    processes: [Process!]!
}

type Process {
    id: ID!
    workflowId: ID!
    status: ProcessStatus!
    formData: JSON!
    state: JSON!
    createdAt: DateTime!
    updatedAt: DateTime!
    startedAt: DateTime
    completedAt: DateTime
    steps: [ProcessStep!]!
}

type ProcessStep {
    id: ID!
    processId: ID!
    stepName: String!
    status: ProcessStatus!
    inputData: JSON!
    outputData: JSON!
    errorMessage: String
    startedAt: DateTime
    completedAt: DateTime
}

enum ProcessStatus {
    CREATED
    RUNNING
    COMPLETED
    FAILED
    CANCELLED
}
```

#### 5.2.2 Queries and Mutations
```graphql
type Query {
    workflows: [Workflow!]!
    workflow(name: String!): Workflow
    processes(status: ProcessStatus): [Process!]!
    process(id: ID!): Process
}

type Mutation {
    startWorkflow(name: String!, formData: JSON!): Process!
    cancelProcess(id: ID!): Boolean!
}

type Subscription {
    processUpdates(processId: ID!): Process!
    workflowEvents: WorkflowEvent!
}
```

---

## 6. Service Layer Architecture

### 6.1 Service Layer Pattern

#### 6.1.1 Workflow Service
```python
class WorkflowService:
    """Core workflow management service"""
    
    def __init__(self, db: Database, redis: Redis):
        self.db = db
        self.redis = redis
        self.logger = structlog.get_logger(__name__)
    
    async def start_workflow(
        self,
        workflow_name: str,
        form_data: Dict[str, Any]
    ) -> ProcessInstance:
        """Start workflow execution"""
        # 1. Validate workflow exists
        workflow = await self.get_workflow(workflow_name)
        if not workflow:
            raise WorkflowNotFoundError(workflow_name)
        
        # 2. Create process instance
        process = ProcessInstance(
            workflow_id=workflow.id,
            status=WorkflowStatus.CREATED,
            form_data=form_data
        )
        
        # 3. Persist to database
        saved_process = await self.db.create_process(process)
        
        # 4. Queue for execution
        await self.redis.lpush("workflow_queue", saved_process.id)
        
        # 5. Update status
        saved_process.status = WorkflowStatus.RUNNING
        await self.db.update_process(saved_process)
        
        return saved_process
    
    async def execute_workflow(self, process_id: str):
        """Execute workflow steps"""
        process = await self.db.get_process(process_id)
        workflow = await self.get_workflow(process.workflow_id)
        
        try:
            # Execute workflow steps
            for step in workflow.steps:
                await self.execute_step(process, step)
            
            # Mark as completed
            process.status = WorkflowStatus.COMPLETED
            process.completed_at = datetime.utcnow()
            
        except Exception as e:
            process.status = WorkflowStatus.FAILED
            self.logger.error("Workflow execution failed", 
                            process_id=process_id, error=str(e))
        
        finally:
            await self.db.update_process(process)
```

#### 6.1.2 NetBox Integration Service
```python
class NetBoxService:
    """NetBox API integration service"""
    
    def __init__(self, config: NetBoxConfig):
        self.api = NetBoxAPI(
            url=config.url,
            token=config.token
        )
        self.logger = structlog.get_logger(__name__)
    
    async def create_manufacturer(
        self,
        payload: ManufacturerPayload
    ) -> Dict[str, Any]:
        """Create manufacturer in NetBox"""
        try:
            result = await self.api.dcim.manufacturers.create(
                payload.dict()
            )
            self.logger.info("Manufacturer created", 
                           name=payload.name, id=result.id)
            return result
        
        except NetBoxAPIException as e:
            self.logger.error("Failed to create manufacturer",
                            name=payload.name, error=str(e))
            raise
    
    async def get_manufacturers(self) -> List[Dict[str, Any]]:
        """Get all manufacturers from NetBox"""
        return await self.api.dcim.manufacturers.all()
    
    async def manufacturer_exists(self, slug: str) -> bool:
        """Check if manufacturer exists"""
        try:
            result = await self.api.dcim.manufacturers.get(slug=slug)
            return result is not None
        except NetBoxAPIException:
            return False
```

---

## 7. Error Handling Strategy

### 7.1 Error Classification

#### 7.1.1 Error Types
```python
class WorkflowError(Exception):
    """Base workflow error"""
    pass

class ValidationError(WorkflowError):
    """Data validation errors"""
    pass

class IntegrationError(WorkflowError):
    """External system integration errors"""
    pass

class ResourceError(WorkflowError):
    """Resource availability errors"""
    pass

class ConfigurationError(WorkflowError):
    """System configuration errors"""
    pass
```

### 7.2 Error Handling Patterns

#### 7.2.1 Retry Logic
```python
import asyncio
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                    continue
            
            raise last_exception
        return wrapper
    return decorator

# Usage
class NetBoxService:
    @retry(max_attempts=3, delay=1.0)
    async def create_manufacturer(self, payload):
        return await self.api.dcim.manufacturers.create(payload)
```

#### 7.2.2 Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise IntegrationError("Service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

### 7.3 Error Response Format

#### 7.3.1 Standardized Error Responses
```python
class ErrorResponse(BaseModel):
    """Standardized error response format"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request correlation ID")

# FastAPI error handler
@app.exception_handler(WorkflowError)
async def workflow_error_handler(request: Request, exc: WorkflowError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc),
            request_id=request.headers.get("X-Request-ID")
        ).dict()
    )
```

---

## 8. Configuration Management

### 8.1 Environment Configuration

#### 8.1.1 Configuration Schema
```python
class DatabaseConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="orchestrator-core")
    username: str = Field(default="nwa")
    password: str = Field(default="nwa")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class NetBoxConfig(BaseModel):
    url: str = Field(..., description="NetBox instance URL")
    token: str = Field(..., description="NetBox API token")
    verify_ssl: bool = Field(default=True)
    timeout: int = Field(default=30)

class RedisConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    database: int = Field(default=0)
    password: Optional[str] = None

class AppConfig(BaseModel):
    """Main application configuration"""
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    cors_origins: List[str] = Field(default_factory=list)
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    netbox: NetBoxConfig
```

#### 8.1.2 Configuration Loading
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
    
    @classmethod
    def load(cls) -> AppConfig:
        """Load configuration from environment"""
        settings = cls()
        return AppConfig(**settings.dict())

# Global configuration instance
config = Settings.load()
```

---

## 9. Security Implementation

### 9.1 Security Architecture
*[Placeholder for future security implementation]*

#### 9.1.1 Authentication Framework
- JWT token-based authentication
- Integration with enterprise identity providers (LDAP/SAML)
- API key authentication for service-to-service calls

#### 9.1.2 Authorization Framework
- Role-based access control (RBAC)
- Permission-based resource access
- Workflow execution permissions

#### 9.1.3 Data Protection
- TLS encryption for all API communications
- Database encryption at rest
- Secure credential storage (HashiCorp Vault integration)

### 9.2 Security Headers and Middleware
*[Placeholder for future security implementation]*

```python
# Security middleware configuration
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

---

## 10. Performance Optimization

### 10.1 Database Optimization

#### 10.1.1 Index Strategy
```sql
-- Performance indexes
CREATE INDEX idx_processes_status ON processes(status);
CREATE INDEX idx_processes_workflow_id ON processes(workflow_id);
CREATE INDEX idx_processes_created_at ON processes(created_at DESC);
CREATE INDEX idx_process_steps_process_id ON process_steps(process_id);
CREATE INDEX idx_audit_log_process_id ON audit_log(process_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
```

#### 10.1.2 Connection Pool Configuration
```python
# SQLAlchemy engine configuration
engine = create_async_engine(
    database_url,
    pool_size=10,           # Base pool size
    max_overflow=20,        # Additional connections
    pool_timeout=30,        # Connection timeout
    pool_recycle=3600,      # Recycle connections hourly
    echo=config.debug       # SQL logging in debug mode
)
```

### 10.2 Caching Strategy

#### 10.2.1 Redis Caching
```python
class CacheManager:
    """Redis-based caching manager"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.default_ttl = 3600  # 1 hour
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ):
        """Get from cache or execute factory function"""
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Cache miss - execute factory
        value = await factory()
        await self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(value, default=str)
        )
        return value
```

### 10.3 Async Processing

#### 10.3.1 Background Task Processing
```python
import asyncio
from asyncio import Queue

class TaskProcessor:
    """Asynchronous task processor"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.queue = Queue()
        self.workers = []
    
    async def start(self):
        """Start worker pool"""
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def _worker(self, name: str):
        """Worker coroutine"""
        while True:
            try:
                task_func, args, kwargs = await self.queue.get()
                await task_func(*args, **kwargs)
                self.queue.task_done()
            except Exception as e:
                logger.error("Task processing failed", worker=name, error=str(e))
    
    async def submit(self, task_func, *args, **kwargs):
        """Submit task for processing"""
        await self.queue.put((task_func, args, kwargs))
```

---

## 11. Testing Strategy

### 11.1 Test Architecture

#### 11.1.1 Test Categories
- **Unit Tests**: Individual function and class testing
- **Integration Tests**: Service integration testing
- **API Tests**: Endpoint testing with test client
- **Workflow Tests**: End-to-end workflow execution
- **Performance Tests**: Load and stress testing

#### 11.1.2 Test Framework Setup
```python
# pytest configuration
import pytest
import asyncio
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def event_loop():
    """Event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Test database container"""
    with PostgresContainer("postgres:14") as postgres:
        # Run migrations
        # Return connection string
        yield postgres.get_connection_url()

@pytest.fixture
async def test_client(test_db):
    """Test HTTP client"""
    app.dependency_overrides[get_database] = lambda: test_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### 11.2 Test Implementation Examples

#### 11.2.1 Unit Test Example
```python
class TestWorkflowService:
    """Workflow service unit tests"""
    
    @pytest.mark.asyncio
    async def test_start_workflow_success(self, mock_db, mock_redis):
        """Test successful workflow start"""
        # Arrange
        service = WorkflowService(mock_db, mock_redis)
        workflow_name = "test_workflow"
        form_data = {"param": "value"}
        
        # Act
        result = await service.start_workflow(workflow_name, form_data)
        
        # Assert
        assert result.status == WorkflowStatus.RUNNING
        assert result.form_data == form_data
        mock_db.create_process.assert_called_once()
        mock_redis.lpush.assert_called_once()
```

#### 11.2.2 API Test Example
```python
class TestWorkflowAPI:
    """Workflow API integration tests"""
    
    @pytest.mark.asyncio
    async def test_start_workflow_endpoint(self, test_client):
        """Test workflow start endpoint"""
        # Arrange
        payload = {
            "selected_vendors": ["Cisco", "HP"]
        }
        
        # Act
        response = await test_client.post(
            "/api/workflows/task_import_vendors",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "id" in data
```

---

## 12. Monitoring and Observability

### 12.1 Logging Framework

#### 12.1.1 Structured Logging
```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

# Usage example
logger = structlog.get_logger(__name__)
logger.info("Workflow started", 
           workflow_name="test_workflow",
           process_id="123e4567-e89b-12d3-a456-426614174000",
           user_id="admin")
```

#### 12.1.2 Correlation ID Middleware
```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to all requests"""
    
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Add to context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
```

### 12.2 Health Monitoring

#### 12.2.1 Health Check Implementation
```python
class HealthChecker:
    """System health monitoring"""
    
    def __init__(self, db: Database, redis: Redis, netbox: NetBoxService):
        self.db = db
        self.redis = redis
        self.netbox = netbox
    
    async def check_all(self) -> Dict[str, Any]:
        """Check all system components"""
        checks = {
            "database": await self._check_database(),
            "redis": await self._check_redis(),
            "netbox": await self._check_netbox()
        }
        
        overall_status = "healthy" if all(
            check["status"] == "healthy" for check in checks.values()
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            await self.db.execute("SELECT 1")
            return {"status": "healthy", "response_time": "< 50ms"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

---

## 13. External System References

### 13.1 NetBox API Documentation
- **Base URL**: Configurable NetBox instance URL
- **Authentication**: Token-based API authentication
- **API Version**: NetBox 3.x REST API
- **Documentation**: https://netbox.readthedocs.io/en/stable/integrations/rest-api/
- **Rate Limiting**: Configurable request throttling
- **Error Codes**: Standard HTTP status codes with NetBox-specific error messages

### 13.2 Devicetype-Library Reference
- **Repository**: https://github.com/netbox-community/devicetype-library
- **Format**: YAML-based device definitions
- **Schema**: Community-maintained device type specifications
- **Update Frequency**: Regular community contributions
- **Validation**: YAML schema validation before import

### 13.3 Orchestrator Core Framework
- **Framework**: https://github.com/workfloworchestrator/orchestrator-core
- **Version**: 4.0.4
- **Documentation**: Framework-specific workflow patterns
- **Form System**: Pydantic-based dynamic form generation
- **State Management**: Built-in workflow state persistence

---

## 14. Deployment and Operations

### 14.1 Container Configuration

#### 14.1.1 Docker Compose Services
```yaml
services:
  orchestrator:
    image: orchestrator:latest
    environment:
      - DATABASE_URL=postgresql://nwa:nwa@postgres:5432/orchestrator-core
      - REDIS_URL=redis://redis:6379/0
      - NETBOX_URL=${NETBOX_URL}
      - NETBOX_TOKEN=${NETBOX_TOKEN}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./devicetype-library:/home/orchestrator/devicetype-library:ro
    
  orchestrator-ui:
    image: orchestrator-ui:latest
    environment:
      - REACT_APP_API_URL=http://localhost:8080
    depends_on:
      - orchestrator
    
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=orchestrator-core
      - POSTGRES_USER=nwa
      - POSTGRES_PASSWORD=nwa
    volumes:
      - postgres-data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
```

### 14.2 Environment Variables

#### 14.2.1 Configuration Variables
```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=orchestrator-core
DATABASE_USER=nwa
DATABASE_PASSWORD=nwa

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DATABASE=0

# NetBox Integration
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your-netbox-api-token
NETBOX_VERIFY_SSL=true
NETBOX_TIMEOUT=30

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Security (Future)
JWT_SECRET_KEY=your-jwt-secret
SESSION_TIMEOUT=3600
```

---

## 15. Future Enhancements

### 15.1 Technical Roadmap

#### 15.1.1 Phase 2: Enhanced Integration
- **Ansible Integration**: Configuration management workflows
- **Git Integration**: Version-controlled configuration templates
- **LDAP/AD Integration**: Enterprise authentication
- **Webhook System**: External system notifications

#### 15.1.2 Phase 3: Advanced Features
- **Multi-tenancy**: Organization-based resource isolation
- **Workflow Templates**: Reusable workflow definitions
- **Advanced Scheduling**: Cron-based workflow execution
- **Distributed Processing**: Multi-node workflow execution

#### 15.1.3 Phase 4: Intelligence Layer
- **ML-based Optimization**: Workflow performance optimization
- **Predictive Analytics**: Resource usage forecasting
- **Anomaly Detection**: Automated error pattern detection
- **Intent Recognition**: Natural language workflow creation

---

## 16. Appendices

### 16.1 Code Style Guidelines
- **Python**: PEP 8 compliance with black formatting
- **TypeScript**: ESLint + Prettier configuration
- **Documentation**: Google-style docstrings
- **Naming**: Clear, descriptive variable and function names

### 16.2 Database Migration Strategy
- **Tool**: Alembic for schema migrations
- **Versioning**: Sequential migration versioning
- **Rollback**: All migrations must support rollback
- **Testing**: Migration testing in CI/CD pipeline

### 16.3 API Versioning Strategy
- **Approach**: URL-based versioning (/api/v1/)
- **Compatibility**: Backward compatibility maintenance
- **Deprecation**: 6-month deprecation notice for breaking changes
- **Documentation**: Version-specific API documentation

---

*Document End*
