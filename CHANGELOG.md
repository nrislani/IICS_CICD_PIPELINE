# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-19

### Added
- **Configuration Module** (`config.py`): Centralized environment configuration with dataclass-based settings
- **Custom Exceptions** (`exceptions.py`): Specific error types for authentication, jobs, pulls, and configuration
- **Retry Logic**: Automatic retry with exponential backoff using `tenacity` library
- **Type Hints**: Full typing annotations across all modules
- **Unit Tests**: Comprehensive test suite with `pytest` and fixtures
- **Project Configuration**: `pyproject.toml` with ruff, black, pytest, and coverage settings
- **Resource Type Input**: Workflow now accepts `resource_type` parameter (MTT, DSS, etc.)

### Changed
- **Python Version**: Pinned to 3.11 for reproducible builds (was 3.x)
- **IICSClient**: Complete refactor with improved error handling and documentation
- **README**: Enhanced with Mermaid diagram, badges, and comprehensive documentation

### Fixed
- **Critical Bug**: `requests.Exceptions` typo → `requests.RequestException`
- **Placeholder Bug**: Hardcoded `ZZZ` resource type → configurable `RESOURCE_TYPE` env var
- **YAML Structure**: Fixed duplicate default values in workflow inputs

### Removed
- **Dead Code**: Removed empty `rollback_mapping.py` file

## [0.1.0] - Initial Release

### Added
- Basic IICS CI/CD pipeline with GitHub Actions
- Development and UAT environment support
- Mapping task deployment automation
- Basic rollback functionality
