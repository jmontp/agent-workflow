"""
Security utilities for the agent interface management system

Provides validation, sanitization, and security measures for API keys,
configuration data, and user inputs.
"""

import re
import hashlib
import hmac
import secrets
from utils.types import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a security validation"""
    valid: bool
    security_level: SecurityLevel
    errors: List[str]
    warnings: List[str]
    sanitized_data: Optional[Dict[str, Any]] = None
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def is_secure(self) -> bool:
        return self.valid and not self.has_errors()


class APIKeyValidator:
    """Validates and manages API keys securely"""
    
    # Known API key patterns
    API_KEY_PATTERNS = {
        'anthropic': {
            'pattern': r'^sk-ant-[a-zA-Z0-9\-_]{95,}$',
            'description': 'Anthropic API key format',
            'min_length': 100,
            'prefix': 'sk-ant-'
        },
        'openai': {
            'pattern': r'^sk-[a-zA-Z0-9]{48,}$',
            'description': 'OpenAI API key format',
            'min_length': 51,
            'prefix': 'sk-'
        },
        'generic': {
            'pattern': r'^[a-zA-Z0-9\-_]{32,}$',
            'description': 'Generic API key format',
            'min_length': 32,
            'prefix': ''
        }
    }
    
    @classmethod
    def validate_api_key(cls, api_key: str, provider: str = 'anthropic') -> ValidationResult:
        """
        Validate an API key for a specific provider
        
        Args:
            api_key: The API key to validate
            provider: The provider type (anthropic, openai, generic)
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        
        if not api_key:
            return ValidationResult(
                valid=False,
                security_level=SecurityLevel.CRITICAL,
                errors=["API key is required"],
                warnings=[]
            )
        
        if not isinstance(api_key, str):
            return ValidationResult(
                valid=False,
                security_level=SecurityLevel.HIGH,
                errors=["API key must be a string"],
                warnings=[]
            )
        
        # Get pattern for provider
        pattern_info = cls.API_KEY_PATTERNS.get(provider, cls.API_KEY_PATTERNS['generic'])
        
        # Check length
        if len(api_key) < pattern_info['min_length']:
            errors.append(f"API key too short (minimum {pattern_info['min_length']} characters)")
        
        # Check pattern
        if not re.match(pattern_info['pattern'], api_key):
            errors.append(f"Invalid API key format for {provider}")
            errors.append(f"Expected format: {pattern_info['description']}")
        
        # Check for common security issues
        if api_key.lower() in ['test', 'demo', 'example', 'placeholder']:
            errors.append("API key appears to be a placeholder")
        
        # Check for whitespace
        if api_key != api_key.strip():
            warnings.append("API key contains leading/trailing whitespace")
            api_key = api_key.strip()
        
        # Check for repeated characters (possible fake key)
        if len(set(api_key)) < 10:
            warnings.append("API key has low character diversity")
        
        # Determine security level
        if errors:
            security_level = SecurityLevel.HIGH
        elif warnings:
            security_level = SecurityLevel.MEDIUM
        else:
            security_level = SecurityLevel.LOW
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=security_level,
            errors=errors,
            warnings=warnings,
            sanitized_data={'api_key': api_key.strip()} if not errors else None
        )
    
    @classmethod
    def mask_api_key(cls, api_key: str) -> str:
        """
        Mask an API key for safe display
        
        Args:
            api_key: The API key to mask
            
        Returns:
            Masked API key string
        """
        if not api_key or len(api_key) < 8:
            return "***"
        
        # Show first 3 and last 4 characters
        if len(api_key) <= 10:
            return f"{api_key[:2]}***{api_key[-2:]}"
        else:
            return f"{api_key[:3]}...{api_key[-4:]}"
    
    @classmethod
    def hash_api_key(cls, api_key: str, salt: Optional[str] = None) -> str:
        """
        Create a secure hash of an API key for storage/comparison
        
        Args:
            api_key: The API key to hash
            salt: Optional salt (will generate if not provided)
            
        Returns:
            Hashed API key
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for secure hashing
        import hashlib
        key = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt.encode(), 100000)
        return f"{salt}:{key.hex()}"
    
    @classmethod
    def verify_api_key_hash(cls, api_key: str, hashed: str) -> bool:
        """
        Verify an API key against its hash
        
        Args:
            api_key: The API key to verify
            hashed: The stored hash to verify against
            
        Returns:
            True if the API key matches the hash
        """
        try:
            salt, stored_key = hashed.split(':', 1)
            import hashlib
            key = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt.encode(), 100000)
            return hmac.compare_digest(stored_key, key.hex())
        except (ValueError, AttributeError):
            return False


class ConfigurationValidator:
    """Validates interface configuration data"""
    
    # Safe configuration fields
    SAFE_FIELDS = {
        'enabled', 'timeout', 'max_tokens', 'temperature', 'model',
        'response_delay', 'failure_rate', 'endpoint_url'
    }
    
    # Field validation rules
    FIELD_RULES = {
        'timeout': {'type': int, 'min': 10, 'max': 3600},
        'max_tokens': {'type': int, 'min': 1, 'max': 100000},
        'temperature': {'type': float, 'min': 0.0, 'max': 2.0},
        'response_delay': {'type': float, 'min': 0.0, 'max': 60.0},
        'failure_rate': {'type': float, 'min': 0.0, 'max': 1.0},
        'enabled': {'type': bool},
        'model': {'type': str, 'max_length': 100},
        'endpoint_url': {'type': str, 'max_length': 500}
    }
    
    @classmethod
    def validate_configuration(cls, config_data: Dict[str, Any], interface_type: str) -> ValidationResult:
        """
        Validate interface configuration data
        
        Args:
            config_data: Configuration data to validate
            interface_type: Type of interface being configured
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        sanitized_data = {}
        
        if not isinstance(config_data, dict):
            return ValidationResult(
                valid=False,
                security_level=SecurityLevel.HIGH,
                errors=["Configuration must be a dictionary"],
                warnings=[]
            )
        
        # Validate each field
        for field, value in config_data.items():
            if field.startswith('custom_'):
                # Handle custom fields
                custom_field = field[7:]  # Remove 'custom_' prefix
                if custom_field in cls.FIELD_RULES:
                    validation_result = cls._validate_field(custom_field, value)
                    if validation_result.errors:
                        errors.extend([f"custom_{err}" for err in validation_result.errors])
                    if validation_result.warnings:
                        warnings.extend([f"custom_{warn}" for warn in validation_result.warnings])
                    if validation_result.sanitized_data:
                        sanitized_data[field] = validation_result.sanitized_data[custom_field]
                else:
                    warnings.append(f"Unknown custom field: {custom_field}")
                    sanitized_data[field] = value
            elif field == 'api_key':
                # Special handling for API keys
                api_validation = APIKeyValidator.validate_api_key(value, 'anthropic')
                if api_validation.errors:
                    errors.extend(api_validation.errors)
                if api_validation.warnings:
                    warnings.extend(api_validation.warnings)
                if api_validation.sanitized_data:
                    sanitized_data[field] = api_validation.sanitized_data['api_key']
            elif field in cls.SAFE_FIELDS:
                # Validate known safe fields
                validation_result = cls._validate_field(field, value)
                if validation_result.errors:
                    errors.extend(validation_result.errors)
                if validation_result.warnings:
                    warnings.extend(validation_result.warnings)
                if validation_result.sanitized_data:
                    sanitized_data[field] = validation_result.sanitized_data[field]
            else:
                # Unknown field
                warnings.append(f"Unknown configuration field: {field}")
                # Still include it but sanitize the value
                sanitized_data[field] = cls._sanitize_value(value)
        
        # Interface-specific validation
        if interface_type == 'anthropic_api':
            if 'api_key' not in config_data or not config_data['api_key']:
                errors.append("API key is required for Anthropic API interface")
        
        # Determine security level
        if any('api_key' in error for error in errors):
            security_level = SecurityLevel.CRITICAL
        elif errors:
            security_level = SecurityLevel.HIGH
        elif warnings:
            security_level = SecurityLevel.MEDIUM
        else:
            security_level = SecurityLevel.LOW
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=security_level,
            errors=errors,
            warnings=warnings,
            sanitized_data=sanitized_data
        )
    
    @classmethod
    def _validate_field(cls, field: str, value: Any) -> ValidationResult:
        """Validate a single configuration field"""
        errors = []
        warnings = []
        
        if field not in cls.FIELD_RULES:
            return ValidationResult(
                valid=True,
                security_level=SecurityLevel.LOW,
                errors=[],
                warnings=[f"Unknown field: {field}"],
                sanitized_data={field: cls._sanitize_value(value)}
            )
        
        rules = cls.FIELD_RULES[field]
        
        # Type validation
        expected_type = rules['type']
        if not isinstance(value, expected_type):
            try:
                # Try to convert
                if expected_type == int:
                    value = int(value)
                elif expected_type == float:
                    value = float(value)
                elif expected_type == bool:
                    value = bool(value)
                elif expected_type == str:
                    value = str(value)
                else:
                    raise ValueError("Cannot convert")
            except (ValueError, TypeError):
                errors.append(f"{field} must be of type {expected_type.__name__}")
                return ValidationResult(
                    valid=False,
                    security_level=SecurityLevel.MEDIUM,
                    errors=errors,
                    warnings=warnings
                )
        
        # Range validation for numbers
        if expected_type in (int, float):
            if 'min' in rules and value < rules['min']:
                errors.append(f"{field} must be >= {rules['min']}")
            if 'max' in rules and value > rules['max']:
                errors.append(f"{field} must be <= {rules['max']}")
        
        # Length validation for strings
        if expected_type == str:
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f"{field} must be <= {rules['max_length']} characters")
                # Truncate the value
                value = value[:rules['max_length']]
                warnings.append(f"{field} was truncated to {rules['max_length']} characters")
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=SecurityLevel.LOW if not errors else SecurityLevel.MEDIUM,
            errors=errors,
            warnings=warnings,
            sanitized_data={field: value}
        )
    
    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        """Sanitize a value for safe storage"""
        if isinstance(value, str):
            # Remove potentially dangerous characters
            value = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', value)
            # Limit length
            if len(value) > 1000:
                value = value[:1000]
        elif isinstance(value, (int, float)):
            # Ensure reasonable bounds
            if isinstance(value, int):
                value = max(-2147483648, min(2147483647, value))
            else:
                value = max(-1e10, min(1e10, value))
        elif isinstance(value, dict):
            # Recursively sanitize dict values
            return {k: cls._sanitize_value(v) for k, v in value.items() if isinstance(k, str)}
        elif isinstance(value, list):
            # Sanitize list items (limit size)
            return [cls._sanitize_value(item) for item in value[:100]]
        
        return value


class InputSanitizer:
    """Sanitizes user inputs for security"""
    
    @classmethod
    def sanitize_prompt(cls, prompt: str) -> ValidationResult:
        """
        Sanitize a user prompt for agent generation
        
        Args:
            prompt: The user prompt to sanitize
            
        Returns:
            ValidationResult with sanitized prompt
        """
        errors = []
        warnings = []
        
        if not isinstance(prompt, str):
            return ValidationResult(
                valid=False,
                security_level=SecurityLevel.HIGH,
                errors=["Prompt must be a string"],
                warnings=[]
            )
        
        original_prompt = prompt
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'data:text/html',            # Data URLs
            r'vbscript:',                 # VBScript
            r'on\w+\s*=',                 # Event handlers
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, prompt, re.IGNORECASE | re.DOTALL):
                warnings.append(f"Removed potentially dangerous content: {pattern}")
                prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE | re.DOTALL)
        
        # Check prompt length
        if len(prompt) > 10000:
            warnings.append("Prompt was truncated to 10000 characters")
            prompt = prompt[:10000]
        
        # Check for injection attempts
        injection_patterns = [
            r'rm\s+-rf',
            r'sudo\s+',
            r'passwd\s+',
            r'\|\s*sh',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                warnings.append(f"Detected potential command injection pattern: {pattern}")
        
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', prompt)) / max(len(prompt), 1)
        if special_char_ratio > 0.3:
            warnings.append("High ratio of special characters detected")
        
        # Determine security level
        if errors:
            security_level = SecurityLevel.HIGH
        elif len(warnings) > 3:
            security_level = SecurityLevel.MEDIUM
        elif warnings:
            security_level = SecurityLevel.LOW
        else:
            security_level = SecurityLevel.LOW
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=security_level,
            errors=errors,
            warnings=warnings,
            sanitized_data={'prompt': prompt}
        )
    
    @classmethod
    def sanitize_code(cls, code: str) -> ValidationResult:
        """
        Sanitize code input for analysis
        
        Args:
            code: The code to sanitize
            
        Returns:
            ValidationResult with sanitized code
        """
        errors = []
        warnings = []
        
        if not isinstance(code, str):
            return ValidationResult(
                valid=False,
                security_level=SecurityLevel.HIGH,
                errors=["Code must be a string"],
                warnings=[]
            )
        
        # Check code length
        if len(code) > 100000:  # 100KB limit
            warnings.append("Code was truncated to 100KB")
            code = code[:100000]
        
        # Check for obviously malicious patterns
        malicious_patterns = [
            r'import\s+os.*system',
            r'subprocess\.call',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                warnings.append(f"Detected potentially dangerous code pattern: {pattern}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=SecurityLevel.LOW if not warnings else SecurityLevel.MEDIUM,
            errors=errors,
            warnings=warnings,
            sanitized_data={'code': code}
        )


class SecurityAuditor:
    """Performs security audits on interface operations"""
    
    @classmethod
    def audit_interface_operation(cls, operation: str, interface_type: str, 
                                 data: Dict[str, Any], user_context: Dict[str, Any] = None) -> ValidationResult:
        """
        Audit an interface operation for security issues
        
        Args:
            operation: The operation being performed (switch, test, generate, etc.)
            interface_type: The type of interface
            data: Operation data
            user_context: Optional user context
            
        Returns:
            ValidationResult with audit results
        """
        errors = []
        warnings = []
        
        # Rate limiting check (placeholder - would need actual implementation)
        if user_context and user_context.get('request_count', 0) > 100:
            warnings.append("High request rate detected")
        
        # Operation-specific checks
        if operation == 'generate':
            prompt_validation = InputSanitizer.sanitize_prompt(data.get('prompt', ''))
            if prompt_validation.errors:
                errors.extend(prompt_validation.errors)
            if prompt_validation.warnings:
                warnings.extend(prompt_validation.warnings)
        
        elif operation == 'analyze':
            code_validation = InputSanitizer.sanitize_code(data.get('code', ''))
            if code_validation.errors:
                errors.extend(code_validation.errors)
            if code_validation.warnings:
                warnings.extend(code_validation.warnings)
        
        elif operation == 'configure':
            config_validation = ConfigurationValidator.validate_configuration(data, interface_type)
            if config_validation.errors:
                errors.extend(config_validation.errors)
            if config_validation.warnings:
                warnings.extend(config_validation.warnings)
        
        # Interface-specific security checks
        if interface_type == 'anthropic_api' and 'api_key' in data:
            api_validation = APIKeyValidator.validate_api_key(data['api_key'], 'anthropic')
            if api_validation.errors:
                errors.extend(api_validation.errors)
            if api_validation.warnings:
                warnings.extend(api_validation.warnings)
        
        # Determine overall security level
        if errors:
            security_level = SecurityLevel.HIGH
        elif len(warnings) > 5:
            security_level = SecurityLevel.MEDIUM
        elif warnings:
            security_level = SecurityLevel.LOW
        else:
            security_level = SecurityLevel.LOW
        
        return ValidationResult(
            valid=len(errors) == 0,
            security_level=security_level,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def log_security_event(cls, event_type: str, severity: SecurityLevel, 
                          details: Dict[str, Any], user_context: Dict[str, Any] = None):
        """
        Log a security event for monitoring
        
        Args:
            event_type: Type of security event
            severity: Severity level
            details: Event details
            user_context: Optional user context
        """
        log_entry = {
            'event_type': event_type,
            'severity': severity.value,
            'timestamp': logger.handlers[0].formatter.formatTime(logging.LogRecord(
                name=logger.name, level=logging.INFO, pathname='', lineno=0,
                msg='', args=(), exc_info=None
            )) if logger.handlers else 'unknown',
            'details': details,
            'user_context': user_context or {}
        }
        
        if severity in (SecurityLevel.HIGH, SecurityLevel.CRITICAL):
            logger.error(f"Security event: {log_entry}")
        elif severity == SecurityLevel.MEDIUM:
            logger.warning(f"Security event: {log_entry}")
        else:
            logger.info(f"Security event: {log_entry}")


# Security utility functions for easy import
def validate_api_key(api_key: str, provider: str = 'anthropic') -> ValidationResult:
    """Validate an API key"""
    return APIKeyValidator.validate_api_key(api_key, provider)

def mask_api_key(api_key: str) -> str:
    """Mask an API key for display"""
    return APIKeyValidator.mask_api_key(api_key)

def validate_configuration(config_data: Dict[str, Any], interface_type: str) -> ValidationResult:
    """Validate configuration data"""
    return ConfigurationValidator.validate_configuration(config_data, interface_type)

def sanitize_prompt(prompt: str) -> ValidationResult:
    """Sanitize user prompt"""
    return InputSanitizer.sanitize_prompt(prompt)

def sanitize_code(code: str) -> ValidationResult:
    """Sanitize code input"""
    return InputSanitizer.sanitize_code(code)

def audit_operation(operation: str, interface_type: str, data: Dict[str, Any], 
                   user_context: Dict[str, Any] = None) -> ValidationResult:
    """Audit an interface operation"""
    return SecurityAuditor.audit_interface_operation(operation, interface_type, data, user_context)