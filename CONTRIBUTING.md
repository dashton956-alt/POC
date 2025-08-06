# Contributing to NetBox Orchestrator POC

Thank you for your interest in contributing to the NetBox Orchestrator POC! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## 🤝 Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you agree to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- Docker and Docker Compose installed
- Python 3.8+ with pip
- Git configured with your credentials
- Basic understanding of NetBox and network automation
- Familiarity with containerized applications

### Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/POC.git
   cd POC
   ```

2. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Development Services**
   ```bash
   # NetBox
   cd netbox
   docker-compose up -d
   
   # Orchestrator
   cd ../example-orchestrator
   docker-compose up -d
   ```

4. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

## 🛠️ Development Setup

### Project Structure

```
POC/
├── netbox/                     # NetBox configuration
├── example-orchestrator/       # Orchestrator service
├── devicetype-library/         # Device type definitions
├── device_import.py           # Import utility
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── docs/                     # Additional documentation
```

### Local Development

#### NetBox Development
- NetBox runs on port 8000
- Admin interface: http://localhost:8000/admin/
- API: http://localhost:8000/api/
- Default login: admin/admin (change immediately)

#### Orchestrator Development
- API runs on port 8080
- UI runs on port 3000
- GraphQL playground: http://localhost:8080/api/graphql
- Health check: http://localhost:8080/health

### Database Access

```bash
# NetBox database
docker exec -it netbox-postgres-1 psql -U netbox

# Orchestrator database
docker exec -it postgres psql -U orchestrator
```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

1. **Bug Reports**: Help us identify and fix issues
2. **Feature Requests**: Suggest new functionality
3. **Code Contributions**: Submit bug fixes or new features
4. **Documentation**: Improve or add documentation
5. **Device Types**: Add new device definitions
6. **Testing**: Add or improve test coverage

### Contribution Areas

#### NetBox Integration
- API client improvements
- New NetBox features integration
- Performance optimizations
- Error handling enhancements

#### Orchestrator Features
- New workflow types
- Enhanced GraphQL schema
- Service integrations
- UI improvements

#### Device Type Library
- New vendor support
- Device definition updates
- Schema improvements
- Validation enhancements

#### Documentation
- Setup guides
- API documentation
- Troubleshooting guides
- Best practices

## 🔄 Pull Request Process

### Before Submitting

1. **Check Existing Issues**: Search for existing issues or PRs
2. **Create an Issue**: For significant changes, create an issue first
3. **Fork the Repository**: Work on your own fork
4. **Create Feature Branch**: Use descriptive branch names

### Pull Request Steps

1. **Prepare Your Changes**
   ```bash
   git checkout -b feature/your-feature-name
   # Make your changes
   git add .
   git commit -m "feat: add your feature description"
   ```

2. **Test Your Changes**
   ```bash
   # Run tests
   python -m pytest tests/
   
   # Test device import
   python device_import.py --dry-run
   
   # Check containers
   docker ps
   ```

3. **Update Documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

4. **Submit Pull Request**
   - Use descriptive title and description
   - Reference related issues
   - Include testing information
   - Add screenshots for UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] New tests added (if applicable)
- [ ] Manual testing completed

## Related Issues
Fixes #issue-number

## Screenshots (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## 🐛 Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Clear Title**: Descriptive issue title
2. **Environment Details**: OS, Docker version, browser
3. **Steps to Reproduce**: Exact steps to trigger the bug
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Logs**: Relevant log output
7. **Screenshots**: If applicable

### Feature Requests

For feature requests, provide:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other solutions considered
4. **Additional Context**: Any other relevant information

### Issue Labels

We use labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `priority-high`: High priority issue
- `netbox`: NetBox-related
- `orchestrator`: Orchestrator-related

## 📏 Code Standards

### Python Style

- Follow PEP 8 style guide
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints where appropriate

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`
- **Docker services**: `kebab-case`

### Documentation Style

- Use Google-style docstrings
- Include type information
- Provide examples for complex functions

```python
def import_device_types(vendor: str = None, dry_run: bool = False) -> int:
    """Import device types from the library.
    
    Args:
        vendor: Specific vendor to import (optional)
        dry_run: If True, don't actually import
        
    Returns:
        Number of device types imported
        
    Example:
        >>> count = import_device_types(vendor="cisco")
        >>> print(f"Imported {count} device types")
    """
```

### Git Commit Messages

Use conventional commit format:

```
type(scope): description

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(orchestrator): add device provisioning workflow
fix(netbox): resolve Redis connection timeout
docs(readme): add installation troubleshooting
```

## 🧪 Testing

### Test Types

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **API Tests**: Test API endpoints

### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_device_import.py

# With coverage
python -m pytest --cov=. --cov-report=html

# Integration tests
python -m pytest tests/integration/
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_device_import_success():
    """Test successful device import."""
    with patch('pynetbox.api') as mock_api:
        mock_api.return_value.dcim.device_types.create.return_value = Mock(id=1)
        result = import_device_types(vendor="cisco")
        assert result > 0

def test_device_import_dry_run():
    """Test dry run mode."""
    result = import_device_types(dry_run=True)
    assert result == 0  # Should not import in dry run
```

### Test Coverage

- Maintain minimum 80% test coverage
- Focus on critical path testing
- Include edge cases and error conditions
- Test API integrations with mocks

## 📚 Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and comments
2. **API Documentation**: GraphQL schema and REST endpoints
3. **User Documentation**: Setup and usage guides
4. **Developer Documentation**: Contributing and development guides

### Documentation Standards

- Keep documentation up to date with code changes
- Use clear, concise language
- Include examples and code snippets
- Provide troubleshooting information

### Building Documentation

```bash
# Generate API docs (if available)
sphinx-build -b html docs/ docs/_build/

# Update README
# Edit README.md directly

# Validate markdown
markdownlint README.md CONTRIBUTING.md
```

## 🔒 Security

### Security Considerations

- Never commit sensitive information (passwords, tokens)
- Use environment variables for configuration
- Follow principle of least privilege
- Validate all inputs
- Use secure communication protocols

### Reporting Security Issues

For security vulnerabilities:

1. **Do NOT** create a public issue
2. Email the maintainers directly
3. Provide detailed information
4. Allow time for assessment and fixes

## 🏷️ Release Process

### Version Numbering

We follow Semantic Versioning (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Test all functionality
4. Create release tag
5. Update documentation
6. Announce release

## 📞 Getting Help

### Community Resources

- **GitHub Issues**: https://github.com/dashton956-alt/POC/issues
- **Discussions**: https://github.com/dashton956-alt/POC/discussions
- **NetBox Community**: https://netdev.chat/

### Development Questions

For development questions:

1. Check existing documentation
2. Search closed issues
3. Ask in discussions
4. Create a new issue if needed

## 🙏 Recognition

We appreciate all contributions and will recognize contributors in:

- CHANGELOG.md
- README.md acknowledgments
- Release notes
- Project documentation

Thank you for contributing to the NetBox Orchestrator POC!
