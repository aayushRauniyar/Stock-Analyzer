# Testing Practices

## Frameworks
- `pytest` for backend execution tests (`test_phase5_integration.py`, `test_phase5_module1.py`, `test_phase5_module3.py`).

## Mocks & Dependencies
- Mostly end-to-end integration tests pulling real APIs against the `paper-api.alpaca.markets/v2` sandbox environment for dry-runs.
- Testing the REST Flask container mostly using standard `requests` / internal test runners (e.g. `verify_endpoints.py`).

## CI/CD 
- Scripted batch files for execution locally (`test_module1.bat`).
