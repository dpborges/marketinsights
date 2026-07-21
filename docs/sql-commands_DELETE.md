### Sector snapshot view
```SELECT * 
FROM vw_sector_performance_snapshot
WHERE as_of_date = CURRENT_DATE;
```
Used instead of repeatedly joining:

- fact_sector_performance_snapshot
- dim_date
- dim_sector
