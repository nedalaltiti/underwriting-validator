# Underwriting Validation API

A FastAPI service for contact validation with hardship, budget, and address analysis.

## Features

- **Eligibility Check**: Verify if contacts meet validation criteria
- **Combined Validation**: Hardship + budget + address analysis
- **AI-Powered Analysis**: Gemini integration for hardship validation
- **Database Integration**: PostgreSQL for contact data

## API Endpoints

- `POST /api/validation/combined` - **Main endpoint**: Combined validation with eligibility check
- `POST /api/validation/contact` - Individual validation
- `GET /api/validation/contact/{contact_id}` - Contact info
- `GET /health` - Health check

## Configuration

Required environment variables:
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` - Database connection
- `GOOGLE_API_KEY` - Gemini AI access
- `HARDSHIP_FINANCIAL_ID`, `HARDSHIP_DESCRIPTION_ID` - Hardship field IDs
- `BUDGET_ACCTID`, `BUDGET_C_TYPE`, `BUDGET_ISCOAPP`, `BUDGET_LEADSTATUS` - Budget validation
- `ADDRESS_ACCTID`, `ADDRESS_C_TYPE`, `ADDRESS_ISCOAPP`, `ADDRESS_LEADSTATUS` - Address validation

## Eligibility Check

Verifies if contacts meet validation criteria:
- Account ID ≠ 5783
- Category = "Underwriting" 
- Not deleted (`del = 'f'`)
- Not co-applicant (`iscoapp = 0`)
- Lead status = "Submitted"

## Address Validation

Checks state/company matching:
- **Clarity**: AL, AK, AZ, AR, CA, CO, DC, FL, ID, IN, KY, MD, MA, MI, MN, MS, MO, MT, NE, NM, NY, NC, OH, OK, SD, TN, TX, UT
- **Concordia**: GA, IL, IA, LA, NV, NJ, PA, PR, VA, WI, WY

## Running

```bash
# Development
poetry install
poetry run python -m underwriting_validation.api

# Production
docker-compose up -d
```

## Validation Results

**Result Types**: `pass`, `no_pass`, `mixed`, `no_data`, `not_eligible`, `error`

**Hardship**: AI analysis with confidence score (0.0-1.0)
**Budget**: Income vs expenses with surplus indication
**Address**: State/company matching validation

### Example Response

```json
{
  "contact_id": 12345,
  "eligibility": "eligible",
  "success": true,
  "combined_result": "pass",
  "eligibility_data": { "contact_category": "Underwriting", "contact_lead_status": "Submitted" },
  "hardship_data": { "hardship_confidence": 0.85, "hardship_validation_result": "pass" },
  "budget_data": { "surplus_indication": "positive", "budget_outcome": "pass" },
  "address_data": { "address_validation_result": "pass" }
}
```

#### **Mixed Results**
```json
{
  "contact_id": 12346,
  "success": true,
  "combined_result": "mixed",
  "combined_result_reason": "Mixed validation results - Passed: hardship; Failed: budget; No data: address",
  "message": "Mixed validation results...",
  "hardship_data": {...},
  "budget_data": {...},
  "address_data": null,
  "error": null
}
```

#### **No Data Available**
```json
{
  "contact_id": 12347,
  "success": false,
  "combined_result": "no_data",
  "combined_result_reason": "No validation data available for any category (hardship, budget, or address)",
  "message": "No data found for this contact",
  "hardship_data": null,
  "budget_data": null,
  "address_data": null,
  "error": "No contact data available"
}
```

## API Usage Examples

### Validate Contact
```bash
curl -X POST "http://localhost:3978/api/validation/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 12345,
    "include_hardship": true,
    "include_budget": true,
    "include_address": true
  }'
```

### Combined Validation
```bash
curl -X POST "http://localhost:3978/api/validation/combined" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 12345
  }'
```

### Get Contact Info
```bash
curl "http://localhost:3978/api/validation/contact/12345"
```

## Health Checks

```bash
# Basic health check
curl "http://localhost:3978/health"

# Database health check
curl "http://localhost:3978/health/database"

# Diagnostic information
curl "http://localhost:3978/health/diagnostic"
``` 