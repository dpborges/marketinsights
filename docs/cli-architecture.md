### The CLI architecture will be compartmentized by domain.

<pre>
File structure will look as follows:
  marketinsights
    src
      mi_sdk
        cli
          main.py
          sector_commands.py
          analyst_commands.py
          earnings_commands.py
          ratings_commands.py
</pre>

### The three layers of the architecture will align by domain

| CLI                    | API            | SDK                          |
|------------------------|----------------|------------------------------|
| `sector_commands.py`   | `sectors.py`   | `sector_summary_service.py`  |
| `analyst_commands.py`  | `analysts.py`  | `analyst_service.py`         |
| `company_commands.py`  | `companies.py` | `company_profile_service.py` |
| `earnings_commands.py` | `earnings.py`  | `earnings_service.py`        |
| `ratings_commands.py`  | `ratings.py`   | `ratings_service.py`         |
| `peer_commands.py`     | `peers.py`     | `peer_comparison_service.py` |

### Both the API and CLI become thin interfaces over the same domain services
```text
              ┌── REST API ──────────┐
              │                      │
User ─────────┤                      ▼
              │              Domain Services
              │                      │
              └── CLI ───────────────┤
                                     ▼
                              Provider Adapter
                                     │
                                     ▼
                                    FMP
```

### Below is example CLI command for the sector_summary_service.py

```bash
market-data sector summary --period 1M
```
