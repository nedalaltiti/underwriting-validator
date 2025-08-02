import logging
import os
import json
import tempfile
from dataclasses import dataclass, field
from typing import Optional, List
from underwriting_validation.config.environment import (
    get_env_var, get_env_var_bool, get_env_var_float, get_env_var_int, get_env_var_list
)

logger = logging.getLogger("underwriting_validation.config")

@dataclass(frozen=True)
class GoogleCredentials:
    """Handles Google Cloud service account credentials from various sources."""
    
    # Credential sources
    json_file_path: Optional[str] = None
    api_key: Optional[str] = None
    temp_credentials_file: Optional[str] = None
    
    # Service account components (for environment variable-based auth)
    service_account_type: Optional[str] = None
    project_id: Optional[str] = None
    private_key_id: Optional[str] = None
    private_key: Optional[str] = None
    client_email: Optional[str] = None
    client_id: Optional[str] = None
    auth_uri: Optional[str] = None
    token_uri: Optional[str] = None
    auth_provider_x509_cert_url: Optional[str] = None
    client_x509_cert_url: Optional[str] = None
    universe_domain: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> "GoogleCredentials":
        """Create credentials from environment variables with fallback priority."""
        logger.debug("Loading Google credentials from environment")
        
        # Check for existing JSON file path first
        json_file_path = get_env_var("GOOGLE_APPLICATION_CREDENTIALS")
        if json_file_path and os.path.exists(json_file_path):
            logger.info("Using existing GOOGLE_APPLICATION_CREDENTIALS file")
            return cls(json_file_path=json_file_path)
        
        # Check for individual service account environment variables
        service_account_vars = {
            'service_account_type': get_env_var('GOOGLE_SERVICE_ACCOUNT_TYPE'),
            'project_id': get_env_var('GOOGLE_SERVICE_ACCOUNT_PROJECT_ID'),
            'private_key_id': get_env_var('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID'),
            'private_key': get_env_var('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY'),
            'client_email': get_env_var('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL'),
            'client_id': get_env_var('GOOGLE_SERVICE_ACCOUNT_CLIENT_ID'),
            'auth_uri': get_env_var('GOOGLE_SERVICE_ACCOUNT_AUTH_URI'),
            'token_uri': get_env_var('GOOGLE_SERVICE_ACCOUNT_TOKEN_URI'),
        }
        
        # Check if we have the minimum required service account fields
        required_fields = ['service_account_type', 'project_id', 'private_key', 'client_email']
        has_service_account = all(service_account_vars.get(field) for field in required_fields)
        
        if has_service_account:
            logger.info("Using service account credentials from environment variables")
            return cls(
                service_account_type=service_account_vars['service_account_type'],
                project_id=service_account_vars['project_id'], 
                private_key_id=service_account_vars['private_key_id'],
                private_key=service_account_vars['private_key'],
                client_email=service_account_vars['client_email'],
                client_id=service_account_vars['client_id'],
                auth_uri=service_account_vars['auth_uri'] or 'https://accounts.google.com/o/oauth2/auth',
                token_uri=service_account_vars['token_uri'] or 'https://oauth2.googleapis.com/token',
                auth_provider_x509_cert_url=get_env_var(
                    'GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL',
                    'https://www.googleapis.com/oauth2/v1/certs'
                ),
                client_x509_cert_url=get_env_var('GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL'),
                universe_domain=get_env_var('GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN', 'googleapis.com')
            )
        
        # Fallback to API key
        api_key = get_env_var("GOOGLE_API_KEY")
        if api_key:
            logger.info("Using Google API key for authentication")
            return cls(api_key=api_key)
        
        # No credentials found
        logger.warning("No Google credentials found in environment")
        return cls()
    
    def create_credentials_file(self) -> Optional[str]:
        """Create a temporary credentials file from environment variables if needed."""
        if self.json_file_path:
            return self.json_file_path
            
        if not self._has_service_account_credentials():
            return None
            
        try:
            # Create the service account credentials dictionary
            credentials_dict = {
                "type": self.service_account_type,
                "project_id": self.project_id,
                "private_key_id": self.private_key_id,
                "private_key": self.private_key.replace('\\n', '\n') if self.private_key else None,
                "client_email": self.client_email,
                "client_id": self.client_id,
                "auth_uri": self.auth_uri,
                "token_uri": self.token_uri,
                "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
                "client_x509_cert_url": self.client_x509_cert_url,
                "universe_domain": self.universe_domain
            }
            
            # Create a temporary file to store the credentials
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            json.dump(credentials_dict, temp_file, indent=2)
            temp_file.flush()
            temp_file.close()
            
            logger.info(f"Created temporary service account credentials file")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to create temporary credentials file: {e}")
            return None
    
    def _has_service_account_credentials(self) -> bool:
        """Check if we have the minimum required service account credentials."""
        return bool(
            self.service_account_type and 
            self.project_id and 
            self.private_key and 
            self.client_email
        )
    
    @property
    def has_credentials(self) -> bool:
        """Check if we have any valid credentials."""
        return bool(
            self.json_file_path or 
            self.api_key or 
            self._has_service_account_credentials()
        )
    
    @property
    def auth_method(self) -> str:
        """Get the authentication method being used."""
        if self.json_file_path:
            return "service_account_file"
        elif self._has_service_account_credentials():
            return "service_account_env"
        elif self.api_key:
            return "api_key"
        else:
            return "none"

@dataclass(frozen=True)
class DatabaseSettings:
    name: str
    user: str
    password: str
    host: str
    port: int
    sslmode: str = "disable"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    
    @property
    def url(self) -> str:
        """
        Assemble a SQLAlchemy URL using asyncpg.  
        Example: postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=disable
        """
        creds = f"{self.user}:{self.password}" if self.password else self.user
        return (
            f"postgresql+asyncpg://{creds}@{self.host}:{self.port}/{self.name}"
        )

    def get_sanitized_url(self) -> str:
        """Get database URL with password masked."""
        if self.password:
            return self.url.replace(self.password, "***")
        return self.url

    @property
    def engine_kwargs(self) -> dict:
        return dict(
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
        )
    
    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        # Get database settings from environment variables
        db_name = get_env_var("DB_NAME") 
        db_user = get_env_var("DB_USER")
        db_password = get_env_var("DB_PASSWORD")
        db_host = get_env_var("DB_HOST")
        
        # Enhanced environment variable debugging
        logger.info(f"=== DATABASE CONFIGURATION ===")
        logger.info(f"DB_NAME: {db_name or 'NOT_SET'}")
        logger.info(f"DB_USER: {db_user or 'NOT_SET'}")
        logger.info(f"DB_PASSWORD: {'SET' if db_password else 'NOT_SET'}")
        logger.info(f"DB_HOST: {db_host or 'NOT_SET'}")
        
        # Validate required environment variables
        if not all([db_name, db_user, db_password, db_host]):
            missing = [name for name, val in [("DB_NAME", db_name), ("DB_USER", db_user), 
                                            ("DB_PASSWORD", db_password), ("DB_HOST", db_host)] if not val]
            raise ValueError(f"Missing required database environment variables: {missing}")
            
        result = cls(
            name=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=get_env_var_int("DB_PORT", 5432),
            sslmode=get_env_var("DB_SSLMODE", "disable"),
            pool_size=get_env_var_int("DB_POOL_SIZE", 5),
            max_overflow=get_env_var_int("DB_MAX_OVERFLOW", 10),
            pool_timeout=get_env_var_int("DB_POOL_TIMEOUT", 30),
            pool_recycle=get_env_var_int("DB_POOL_RECYCLE", 1800),
        )
        
        logger.info(f"✅ Database config: host={result.host}, port={result.port}, database={result.name}")
        logger.info(f"Database URL: {result.get_sanitized_url()}")
        return result
    
@dataclass(frozen=True)
class GeminiSettings:
    """Configuration for Google Gemini AI service."""
    model_name: str = "gemini-2.0-flash-001"
    temperature: float = 0.0
    max_output_tokens: int = 1024
    credentials: GoogleCredentials = field(default_factory=GoogleCredentials)

    @classmethod
    def from_environment(cls) -> "GeminiSettings":
        """Create Gemini settings from environment variables."""
        credentials = GoogleCredentials.from_environment()
        
        if not credentials.has_credentials:
            logger.warning("No Google credentials found - Gemini functionality may not work properly")
        else:
            logger.info(f"Gemini authentication method: {credentials.auth_method}")
            
        return cls(
            model_name=get_env_var("GEMINI_MODEL_NAME", cls.model_name),
            temperature=get_env_var_float("GEMINI_TEMPERATURE", cls.temperature),
            max_output_tokens=get_env_var_int("GEMINI_MAX_OUTPUT_TOKENS", cls.max_output_tokens),
            credentials=credentials,
        )
        
    @property
    def has_valid_credentials(self) -> bool:
        """Check if we have valid credentials for Gemini."""
        return self.credentials.has_credentials
        
    @property
    def uses_service_account(self) -> bool:
        """Check if using service account authentication."""
        return self.credentials.auth_method in ["service_account_file", "service_account_env"]
        
    @property
    def uses_api_key(self) -> bool:
        """Check if using API key authentication."""
        return self.credentials.auth_method == "api_key"

@dataclass(frozen=True)
class GoogleCloudSettings:
    project_id: Optional[str] = None
    location: str = "us-central1"

    @classmethod
    def from_environment(cls) -> "GoogleCloudSettings":
        return cls(
            project_id=get_env_var("GOOGLE_CLOUD_PROJECT"),
            location=get_env_var("GOOGLE_CLOUD_LOCATION", cls.location),
        )



@dataclass(frozen=True)
class HardshipFieldSettings:
    """Hardship field ID configuration for database queries."""
    financial_hardship_id: int = 1  # Default value, will be overridden by environment
    hardship_description_id: int = 2  # Default value, will be overridden by environment
    
    @classmethod
    def from_environment(cls) -> "HardshipFieldSettings":
        return cls(
            financial_hardship_id=get_env_var_int("HARDSHIP_FINANCIAL_ID", 1),
            hardship_description_id=get_env_var_int("HARDSHIP_DESCRIPTION_ID", 2),
        )
    
    def validate(self) -> bool:
        """Validate that the field IDs are reasonable values."""
        # Check that IDs are positive integers within reasonable range
        if not (1 <= self.financial_hardship_id <= 999999):
            logger.error(f"Invalid financial hardship ID: {self.financial_hardship_id}")
            return False
        if not (1 <= self.hardship_description_id <= 999999):
            logger.error(f"Invalid hardship description ID: {self.hardship_description_id}")
            return False
        if self.financial_hardship_id == self.hardship_description_id:
            logger.error("Financial hardship ID and hardship description ID cannot be the same")
            return False
        return True

@dataclass(frozen=True)
class BudgetFieldSettings:
    """Budget field ID configuration for database queries."""
    acctid: int = 1  # Default account ID
    c_type: int = 2  # Default contact type
    iscoapp: int = 0  # Default iscoapp value
    leadstatus: int = 3  # Default lead status
    
    @classmethod
    def from_environment(cls) -> "BudgetFieldSettings":
        return cls(
            acctid=get_env_var_int("BUDGET_ACCTID", 1),
            c_type=get_env_var_int("BUDGET_C_TYPE", 2),
            iscoapp=get_env_var_int("BUDGET_ISCOAPP", 0),
            leadstatus=get_env_var_int("BUDGET_LEADSTATUS", 3),
        )
    
    def validate(self) -> bool:
        """Validate that the field values are reasonable."""
        # Check that values are within reasonable ranges
        if not (1 <= self.acctid <= 999999):
            logger.error(f"Invalid budget acctid: {self.acctid}")
            return False
        if not (1 <= self.c_type <= 999999):
            logger.error(f"Invalid budget c_type: {self.c_type}")
            return False
        if not (0 <= self.iscoapp <= 1):
            logger.error(f"Invalid budget iscoapp: {self.iscoapp}")
            return False
        if not (1 <= self.leadstatus <= 999999):
            logger.error(f"Invalid budget leadstatus: {self.leadstatus}")
            return False
        return True

@dataclass(frozen=True)
class AppSettings:
    app_name: str = "Underwriting Validation API"
    app_description: str = "A pure API service for contact validation, providing hardship and budget analysis capabilities."
    host: str = "0.0.0.0"
    port: int = 3978
    debug: bool = False  # Set to False for production
    cors_origins: List[str] = field(default_factory=lambda: ["*"])  # Secure this for production
    db: DatabaseSettings = field(default_factory=DatabaseSettings.from_environment)
    gemini: GeminiSettings = field(default_factory=GeminiSettings.from_environment)
    google_cloud: GoogleCloudSettings = field(default_factory=GoogleCloudSettings.from_environment)
    hardship_fields: HardshipFieldSettings = field(default_factory=HardshipFieldSettings.from_environment)
    budget_fields: BudgetFieldSettings = field(default_factory=BudgetFieldSettings.from_environment)

    @classmethod
    def from_environment(cls) -> "AppSettings":
        # Default CORS origins if not specified in environment
        default_cors_origins = ["*"]
        logger.info("Environment variables loaded; building AppSettings")
        
        # Create hardship field settings and validate them
        hardship_fields = HardshipFieldSettings.from_environment()
        if not hardship_fields.validate():
            raise ValueError("Invalid hardship field configuration")
        
        # Create budget field settings and validate them
        budget_fields = BudgetFieldSettings.from_environment()
        if not budget_fields.validate():
            raise ValueError("Invalid budget field configuration")
        
        logger.info(f"Hardship field configuration: financial_id={hardship_fields.financial_hardship_id}, description_id={hardship_fields.hardship_description_id}")
        logger.info(f"Budget field configuration: acctid={budget_fields.acctid}, c_type={budget_fields.c_type}, iscoapp={budget_fields.iscoapp}, leadstatus={budget_fields.leadstatus}")
        
        return cls(
            db=DatabaseSettings.from_environment(),
            gemini=GeminiSettings.from_environment(),
            google_cloud=GoogleCloudSettings.from_environment(),
            hardship_fields=hardship_fields,
            budget_fields=budget_fields,
            app_name=get_env_var("APP_NAME", cls.app_name),
            app_description=get_env_var("APP_DESCRIPTION", cls.app_description),
            host=get_env_var("HOST", cls.host),
            port=get_env_var_int("PORT", cls.port),
            debug=get_env_var_bool("DEBUG", cls.debug),
            cors_origins=get_env_var_list("CORS_ORIGINS", default_cors_origins),
        )
        
try:
    settings = AppSettings.from_environment()
    logger.info(f"✅ Configuration loaded successfully for '{settings.app_name}'")
    logger.info(f"Database: {settings.db.host}:{settings.db.port}/{settings.db.name}")
    logger.info(f"Gemini API configured: {'Yes' if settings.gemini.has_valid_credentials else 'No'}")
    logger.info(f"Gemini auth method: {settings.gemini.credentials.auth_method}")
except Exception as exc: 
    logger.critical("‼️  Failed to load configuration – exiting", exc_info=exc)
    raise