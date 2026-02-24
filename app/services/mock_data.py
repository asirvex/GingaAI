"""Mock reference data for claim validation.

In production these would come from database tables or external services.
Kept as module-level constants so they're easy to locate and replace.
"""

# Members: member_id -> eligibility status
MEMBERS: dict[str, dict] = {
    "M123": {"name": "Alice Johnson", "status": "active"},
    "M124": {"name": "Bob Smith", "status": "active"},
    "M125": {"name": "Carol White", "status": "inactive"},
    "M126": {"name": "David Brown", "status": "active"},
}

# Providers: provider_id -> provider info
PROVIDERS: dict[str, dict] = {
    "H456": {"name": "City General Hospital", "type": "hospital"},
    "H457": {"name": "Downtown Clinic", "type": "clinic"},
    "H458": {"name": "Specialty Care Center", "type": "specialist"},
}

# Benefit limits per diagnosis code
BENEFIT_LIMITS: dict[str, float] = {
    "D001": 40_000,
    "D002": 60_000,
    "D003": 25_000,
    "D004": 100_000,
}

# Average cost per procedure (used for fraud detection)
PROCEDURE_AVG_COSTS: dict[str, float] = {
    "P001": 20_000,
    "P002": 35_000,
    "P003": 10_000,
    "P004": 50_000,
}
