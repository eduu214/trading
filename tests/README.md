# AlphaStrat Testing Structure

## Test Organization

The AlphaStrat project organizes tests into the following structure:

```
tests/
├── integration/        # Integration and end-to-end tests
│   ├── test_complexity.py
│   └── test_complexity_simple.py
├── scripts/           # Test automation scripts
│   ├── test_complexity_api.sh
│   ├── test_complexity_slice2.sh
│   ├── test_error_handling.sh
│   └── test-scanner.sh
├── docs/              # Test documentation and reports
│   └── test_summary.md
└── README.md          # This file
```

### Component-Specific Tests

- **Backend Tests**: Located in `backend/tests/`
  - Unit tests for FastAPI endpoints
  - Service layer tests
  - Database integration tests
  
- **Frontend Tests**: Located in `frontend/src/__tests__/`
  - React component tests
  - Integration tests
  - E2E tests with Playwright (when added)

### Test File Naming Conventions

- **Python test files**: `test_*.py` or `*_test.py`
- **Shell scripts**: `test*.sh` or `test-*.sh`
- **Documentation**: `*_summary.md` or test reports

### Running Tests

#### Backend Tests
```bash
cd backend
pytest
```

#### Frontend Tests
```bash
cd frontend
npm test
```

#### Integration Test Scripts
```bash
# Run from project root
./tests/scripts/test_complexity_api.sh
./tests/scripts/test_error_handling.sh
```

### Test Categories

1. **Unit Tests**: Test individual functions and components in isolation
2. **Integration Tests**: Test interactions between multiple components
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Test system performance and scalability
5. **Security Tests**: Test authentication, authorization, and security features

### Best Practices

1. **Location**: Place tests close to the code they test when possible
2. **Naming**: Use descriptive names that explain what is being tested
3. **Coverage**: Aim for high test coverage, especially for critical paths
4. **Independence**: Tests should be independent and not rely on execution order
5. **Speed**: Keep unit tests fast, use mocking where appropriate
6. **Documentation**: Document complex test scenarios and setup requirements