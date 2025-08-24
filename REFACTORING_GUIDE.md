# 🔧 Base Classes Implementation Guide

This guide shows how to refactor existing services and repositories to use the new base classes, eliminating DRY violations while preserving the good architecture.

## 📁 Project Structure After Refactoring

```
underwriting_validation/
├── utils/
│   ├── validation_base.py          ✅ CREATED
│   ├── result.py                   ✅ EXISTS  
│   └── pii_filter.py              ✅ EXISTS
├── infrastructure/
│   ├── base/
│   │   ├── __init__.py            ✅ CREATED
│   │   └── repository_base.py     ✅ CREATED
│   └── contract_*_repository.py   ✏️ REFACTOR THESE
├── services/
│   ├── base/
│   │   └── __init__.py            ✅ CREATED
│   └── contract_*_service.py      ✏️ REFACTOR THESE
```

## 🔄 Step-by-Step Refactoring Instructions

### STEP 1: Update Service Imports

**For each `contract_*_validation_service.py` file:**

**BEFORE:**
```python
import logging
from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)
```

**AFTER:**
```python
import logging
from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.validation_base import ContractValidationServiceBase
```

### STEP 2: Update Service Class Declaration

**BEFORE:**
```python
class ContractXValidationService:
    def __init__(self):
        logger.info("ContractXValidationService initialized")
```

**AFTER:**
```python
class ContractXValidationService(ContractValidationServiceBase):
    def __init__(self):
        super().__init__("ContractXValidationService")
    
    def get_validation_type(self) -> str:
        return "X"  # Replace X with actual type (IP, email, signature, etc.)
```

### STEP 3: Update Analysis Methods

**BEFORE:**
```python
async def analyze_x_validity(self, data: XDataIn) -> Result[XAnalysis]:
    try:
        # validation logic here
        analysis = XAnalysis(...)
        
        masked_id = mask_contact_id(contact_id)
        logger.info(f"X analysis completed for contact {masked_id}: {result}")
        return Success(analysis)
    except Exception as e:
        logger.error(f"Error analyzing X validity: {e}")
        return Error(f"Analysis failed: {str(e)}")
```

**AFTER:**
```python
async def analyze_x_validity(self, data: XDataIn) -> Result[XAnalysis]:
    def perform_analysis():
        # validation logic here
        analysis = XAnalysis(...)
        self.log_analysis_completion(data.contact_id, str(analysis.result))
        return analysis
    
    return self.safe_execute("X validation analysis", data.contact_id, perform_analysis)
```

### STEP 4: Update String Normalization

**BEFORE:**
```python
def validate_fields(self, field1: str, field2: str):
    if not field1 or not field2:
        return "Missing Value"
    
    field1 = field1.strip().lower()
    field2 = field2.strip().lower()
    # comparison logic...
```

**AFTER:**
```python
def validate_fields(self, field1: str, field2: str):
    field1_norm = self.normalize_string_field(field1)
    field2_norm = self.normalize_string_field(field2)
    
    if not field1_norm or not field2_norm:
        return "Missing Value"
    # comparison logic...
```

### STEP 5: Update Response Formatting

**BEFORE:**
```python
def format_response(self, analysis):
    if analysis.result == ValidationResult.MATCH:
        return "✅ Success message"
    elif analysis.result == ValidationResult.MISMATCH:
        return "❌ Failure message"
    else:
        return "⚠️ Missing data message"
```

**AFTER:**
```python
def format_response(self, analysis):
    return self.format_validation_response(
        analysis.result,
        "Success message",
        "Failure message", 
        "Missing data message"
    )
```

## 🗄️ Repository Refactoring

### STEP 1: Update Repository Imports

**BEFORE:**
```python
import logging
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)
```

**AFTER:**
```python
import logging
from underwriting_validation.infrastructure.base.repository_base import ContractRepositoryBase
```

### STEP 2: Update Repository Class

**BEFORE:**
```python
class ContractXRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
```

**AFTER:**
```python
class ContractXRepository(ContractRepositoryBase):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "ContractXRepository")
    
    def get_repository_type(self) -> str:
        return "contract_x"
```

### STEP 3: Update Query Execution

**BEFORE:**
```python
async def fetch_data(self, contact_id: int):
    stmt = select(...).where(
        and_(
            Contact.id == bindparam('contact_id'),
            or_(Contact.del_.is_(null()), Contact.del_ != True)
        )
    )
    
    result = await self.session.execute(stmt, {"contact_id": contact_id})
    row = result.fetchone()
    
    if row:
        return dict(row)
    return None
```

**AFTER:**
```python
async def fetch_data(self, contact_id: int):
    stmt = select(...).where(self.create_base_contact_filter(contact_id))
    
    return await self.execute_single_result_query(
        stmt, 
        contact_id, 
        "data fetch operation"
    )
```

## 📋 Files to Refactor

### Services (Apply service refactoring steps):
- ✅ `contract_ip_validation_service.py` (EXAMPLE COMPLETED)
- ⏳ `contract_email_validation_service.py`
- ⏳ `contract_signature_validation_service.py`
- ⏳ `contract_bank_validation_service.py`
- ⏳ `contract_ssn_validation_service.py`
- ⏳ `contract_dob_validation_service.py`
- ⏳ `contract_debts_validation_service.py`
- ⏳ `contract_vlp_validation_service.py`
- ⏳ `contract_gateway_validation_service.py`

### Repositories (Apply repository refactoring steps):
- ✅ `contract_ip_repository.py` (EXAMPLE COMPLETED)
- ⏳ `contract_email_repository.py`
- ⏳ `contract_signature_repository.py`
- ⏳ `contract_bank_repository.py`
- ⏳ `contract_ssn_repository.py`
- ⏳ `contract_dob_repository.py`
- ⏳ `contract_debts_repository.py`
- ⏳ `contract_vlp_repository.py`
- ⏳ `contract_gateway_repository.py`

### Analysis Services (Use AnalysisServiceBase):
- ⏳ `hardship_validation_service.py`
- ⏳ `budget_validation_service.py`
- ⏳ `address_validation_service.py`

## 🎯 Benefits After Refactoring

### Code Reduction:
- **Before**: ~50 lines of repeated error handling per service
- **After**: ~5 lines using base class methods
- **Savings**: 90% reduction in boilerplate code

### Consistency:
- Standardized logging across all services
- Consistent error handling patterns
- Uniform PII masking

### Maintainability:
- Single place to update common functionality
- Easier to add new validation services
- Better testing of shared functionality

## 🧪 Testing the Refactored Code

```python
# Test that base class functionality works
def test_safe_execute():
    service = ContractIPValidationService()
    
    def failing_operation():
        raise ValueError("Test error")
    
    result = service.safe_execute("test", 12345, failing_operation)
    assert result.is_error()
    assert "Test error" in str(result.error)

# Test that PII masking works
def test_pii_masking():
    service = ContractIPValidationService()
    service.log_analysis_completion(1234567890, "test result")
    # Should log: "Analysis completed for contact ***890: test result"
```

## ⚠️ Important Notes

1. **Preserve Business Logic**: Don't change the actual validation logic, only the infrastructure patterns
2. **Keep Tests Working**: Update test imports but keep test logic the same
3. **Gradual Migration**: Refactor one service at a time and test thoroughly
4. **Backward Compatibility**: The public APIs should remain the same

## 🚀 Deployment Strategy

1. **Phase 1**: Create base classes (✅ DONE)
2. **Phase 2**: Refactor 2-3 services as examples
3. **Phase 3**: Test thoroughly in development
4. **Phase 4**: Refactor remaining services in batches
5. **Phase 5**: Update tests and documentation