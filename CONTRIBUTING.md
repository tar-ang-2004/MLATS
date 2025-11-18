# Contributing to ATS Resume Checker

First off, thank you for considering contributing to ATS Resume Checker! 🎉

It's people like you that make ATS Resume Checker such a great tool. We welcome contributions from everyone, whether you're fixing a bug, adding a feature, improving documentation, or just asking questions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@your-domain.com](mailto:conduct@your-domain.com).

## Getting Started

### Ways to Contribute

- 🐛 **Bug Reports**: Found a bug? Let us know!
- 🚀 **Feature Requests**: Have an idea for improvement?
- 📝 **Documentation**: Help improve our docs
- 🧪 **Testing**: Write tests or improve existing ones
- 💻 **Code**: Fix bugs or implement new features
- 🎨 **Design**: Improve UI/UX
- 🌍 **Translation**: Help translate the interface
- 📢 **Outreach**: Share the project with others

### Before You Start

1. **Check existing issues** to see if your bug/feature is already being worked on
2. **Search closed issues** to see if it was already resolved
3. **Start a discussion** for major changes before implementing
4. **Read our documentation** to understand the project structure

## How to Contribute

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork locally
git clone https://github.com/YOUR_USERNAME/ats-resume-checker.git
cd ats-resume-checker

# Add upstream remote
git remote add upstream https://github.com/original-owner/ats-resume-checker.git
```

### 2. Create a Branch

```bash
# Create a new branch for your contribution
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

### 3. Make Changes

Follow our [Development Setup](#development-setup) and [Coding Standards](#coding-standards).

### 4. Test Your Changes

```bash
# Run tests
python -m pytest

# Run linting
flake8 .
black --check .

# Test manually
python app.py
```

### 5. Submit Pull Request

See our [Pull Request Process](#pull-request-process) for detailed steps.

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Redis (optional, for full feature testing)
- PostgreSQL (optional, for production testing)

### Local Setup

```bash
# Clone and navigate to the repository
git clone https://github.com/your-username/ats-resume-checker.git
cd ats-resume-checker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Configure environment
# The .env file contains production defaults - customize as needed
# Edit .env with your local settings

# Initialize database
python init_db.py

# Run the application
python app.py
```

### Development Dependencies

Create `requirements-dev.txt` for development tools:

```txt
# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-flask>=1.2.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.0.0

# Security
bandit>=1.7.0
safety>=2.3.0

# Development Tools
pre-commit>=3.0.0
ipython>=8.0.0
jupyter>=1.0.0

# Load Testing
locust>=2.0.0
```

### IDE Configuration

#### VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### Pre-commit Hooks

Set up pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line Length**: 88 characters (Black's default)
- **Imports**: Use isort for import sorting
- **Docstrings**: Google style docstrings
- **Type Hints**: Use type hints for all functions

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Documentation Standards

#### Function Documentation

```python
def analyze_resume(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Analyze resume against job description using ATS scoring.
    
    Args:
        resume_text: The extracted text content of the resume
        job_description: The target job description for comparison
        
    Returns:
        Dictionary containing analysis results with scores and details
        
    Raises:
        ValueError: If resume_text or job_description is empty
        ProcessingError: If analysis fails due to processing issues
        
    Example:
        >>> result = analyze_resume("John Doe...", "Python Developer...")
        >>> print(result['overall_score'])
        85
    """
    # Implementation here
```

#### Class Documentation

```python
class ResumeProcessor:
    """
    Processes resume files and extracts structured information.
    
    This class handles the parsing and analysis of resume files in various
    formats, extracting contact information, skills, experience, and other
    relevant data for ATS scoring.
    
    Attributes:
        supported_formats: List of supported file formats
        model: The ML model used for text processing
        
    Example:
        >>> processor = ResumeProcessor()
        >>> result = processor.process_file("resume.pdf")
        >>> print(result.skills)
        ['Python', 'Flask', 'SQL']
    """
```

### Error Handling

```python
# Good: Specific exception handling
try:
    result = process_resume(file_path)
except FileNotFoundError:
    logger.error(f"Resume file not found: {file_path}")
    raise ProcessingError("File not found")
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error during processing")
    raise ProcessingError(f"Processing failed: {str(e)}")

# Bad: Generic exception handling
try:
    result = process_resume(file_path)
except Exception as e:
    print(f"Error: {e}")
```

### Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened")
logger.error("A serious problem occurred")
logger.critical("A very serious error occurred")

# Include context in log messages
logger.info(f"Processing resume {filename} for user {user_id}")
logger.error(f"Failed to parse resume {filename}: {error_msg}")
```

## Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_ats_components.py
│   └── test_utils.py
├── integration/          # Integration tests
│   ├── test_api.py
│   ├── test_database.py
│   └── test_processing.py
├── e2e/                 # End-to-end tests
│   └── test_workflows.py
├── fixtures/            # Test data
│   ├── sample_resumes/
│   └── job_descriptions/
└── conftest.py          # Pytest configuration
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from ats_components import ResumeParser

class TestResumeParser:
    """Test suite for ResumeParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        return ResumeParser()
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing."""
        return """
        John Doe
        Software Engineer
        Skills: Python, Flask, SQL
        Experience: 3 years at Tech Corp
        """
    
    def test_parse_skills_extraction(self, parser, sample_resume_text):
        """Test that skills are correctly extracted from resume text."""
        result = parser.parse(sample_resume_text)
        
        assert 'skills' in result
        assert 'Python' in result['skills']
        assert 'Flask' in result['skills']
        assert 'SQL' in result['skills']
    
    def test_parse_empty_text_raises_error(self, parser):
        """Test that parsing empty text raises appropriate error."""
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            parser.parse("")
    
    @patch('ats_components.SentenceTransformer')
    def test_parse_with_mocked_model(self, mock_model, parser, sample_resume_text):
        """Test parsing with mocked ML model."""
        mock_model.return_value.encode.return_value = [[0.1, 0.2, 0.3]]
        
        result = parser.parse(sample_resume_text)
        
        mock_model.assert_called_once()
        assert result is not None
```

#### Integration Test Example

```python
import pytest
from flask import Flask
from models import db, Resume

class TestResumeAPI:
    """Integration tests for Resume API endpoints."""
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def test_analyze_resume_success(self, client, sample_pdf):
        """Test successful resume analysis."""
        response = client.post('/analyze', data={
            'resume': (sample_pdf, 'test_resume.pdf'),
            'job_description': 'Python developer position...'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'overall_score' in data
        assert isinstance(data['overall_score'], int)
    
    def test_analyze_resume_missing_file(self, client):
        """Test analysis with missing file."""
        response = client.post('/analyze', data={
            'job_description': 'Python developer position...'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_ats_components.py

# Run tests matching pattern
pytest -k "test_resume"

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Data

Store test files in `tests/fixtures/`:

```
tests/fixtures/
├── resumes/
│   ├── sample_resume.pdf
│   ├── sample_resume.docx
│   └── malformed_resume.pdf
├── job_descriptions/
│   ├── python_developer.txt
│   └── data_scientist.txt
└── expected_results/
    └── sample_analysis.json
```

## Documentation

### Documentation Types

1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: Endpoint descriptions and examples
3. **User Documentation**: Usage guides and tutorials
4. **Developer Documentation**: Setup and contribution guides

### Writing Documentation

#### README Updates

When adding features, update the README.md:

```markdown
## New Feature Name

Brief description of what the feature does.

### Usage

```python
# Code example
result = new_feature_function(parameters)
```

### Configuration

Add any new environment variables or configuration options.
```

#### API Documentation

Document new endpoints:

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    """
    Brief description of endpoint functionality.
    
    Request Body:
        {
            "parameter1": "Description of parameter1",
            "parameter2": "Description of parameter2"
        }
    
    Response:
        200: Success
            {
                "success": true,
                "data": "Result data"
            }
        400: Bad Request
            {
                "error": "Error description"
            }
    
    Example:
        curl -X POST http://localhost:5000/api/new-endpoint \
             -H "Content-Type: application/json" \
             -d '{"parameter1": "value1"}'
    """
```

## Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Rebase your branch**:
   ```bash
   git checkout feature/your-feature
   git rebase main
   ```

3. **Run tests**:
   ```bash
   pytest
   flake8 .
   black --check .
   ```

4. **Update documentation** if needed

### PR Submission

1. **Create descriptive title**: `feat: add resume batch processing` or `fix: resolve PDF parsing issue`

2. **Write detailed description**:
   ```markdown
   ## Description
   Brief description of changes and motivation.
   
   ## Type of Change
   - [ ] Bug fix (non-breaking change which fixes an issue)
   - [ ] New feature (non-breaking change which adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
   - [ ] Documentation update
   
   ## Testing
   - [ ] Tests pass locally
   - [ ] Added tests for new functionality
   - [ ] Updated documentation
   
   ## Screenshots (if applicable)
   
   ## Additional Notes
   Any additional information or context.
   ```

3. **Link related issues**: "Closes #123" or "Fixes #456"

### PR Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Code Review**: Maintainers review code for quality and standards
3. **Feedback**: Address any comments or requested changes
4. **Approval**: Once approved, PR will be merged

### PR Requirements

- ✅ All tests pass
- ✅ Code follows style guidelines
- ✅ Documentation is updated
- ✅ No merge conflicts
- ✅ Commits are clean and descriptive

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10, Ubuntu 20.04]
 - Python Version: [e.g. 3.9.5]
 - Browser: [e.g. Chrome 91.0]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
A clear and concise description of what you want to happen.

**Motivation**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
A clear and concise description of what you want to happen.

**Alternatives**
A clear and concise description of any alternative solutions or features you've considered.

**Additional Context**
Add any other context or screenshots about the feature request here.
```

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested
- `wontfix`: This will not be worked on

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Email**: [support@your-domain.com](mailto:support@your-domain.com) for private matters

### Getting Help

1. **Check Documentation**: Read the README and docs first
2. **Search Issues**: Look for existing solutions
3. **Ask Questions**: Use GitHub Discussions for questions
4. **Join Community**: Participate in discussions and help others

### Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Annual contributor highlights
- Special recognition for significant contributions

## License

By contributing to ATS Resume Checker, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ATS Resume Checker! 🙏

Your contributions make this project better for everyone. Whether it's a small bug fix or a major feature, every contribution is valued and appreciated.

**Questions?** Don't hesitate to ask! We're here to help you contribute successfully.