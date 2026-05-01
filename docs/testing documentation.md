
### Testing

### Run all fmp adapter mock serivces
pytest tests/test_fmp_adapter.py -v
 
#### How to run test for sector performance
##### From repo root
pytest tests/test_sector_performance_service.py
##### Alternatively
python -m pytest tests/test_sector_performance_service.py
#### How to run test for fmp_adapter
pytest tests/test_fmp_adapter.py -q