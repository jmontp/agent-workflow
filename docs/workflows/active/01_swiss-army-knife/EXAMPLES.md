# Swiss Army Knife Workflow Examples

This document provides real-world examples of the Swiss Army Knife workflow in action, showing typical requests, execution flows, and outcomes.

## Example 1: Generate Fibonacci Function

### Request
"Create a Python function to calculate Fibonacci numbers efficiently"

### Execution Flow

#### 1. IDLE → REQUEST_RECEIVED (0.2s)
```
User Input: "Create a Python function to calculate Fibonacci numbers efficiently"
System: Request received and validated
Request ID: req_fib_001
Estimated complexity: Simple
Estimated duration: 5-10 minutes
```

#### 2. REQUEST_RECEIVED → CONTEXT_SEARCH (2.1s)
```
Searching Context Manager for:
- "fibonacci implementation python"
- "fibonacci optimization patterns"
- "memoization recursive functions"

Found 4 relevant contexts:
1. [0.94] Previous fibonacci with memoization
2. [0.87] Dynamic programming pattern
3. [0.82] Recursive optimization techniques
4. [0.75] Python performance tips
```

#### 3. CONTEXT_SEARCH → EXECUTING (4.8s)
```
Applying patterns:
✓ Memoization decorator pattern
✓ Type hints for clarity
✓ Docstring best practices
✓ Edge case handling (negative numbers)
✓ Unit test generation

Generating implementation...
```

#### 4. EXECUTING → CONTEXT_UPDATE (0.9s)
```
Storing execution result:
- Context ID: ctx_fib_12345
- Patterns applied: 4
- New patterns discovered: 1 (lru_cache usage)
- Confidence: 91%
- Execution time: 4.8s
```

#### 5. CONTEXT_UPDATE → HUMAN_REVIEW (0.1s)
```
Result ready for review
Total execution time: 8.1 seconds
```

### Generated Output

```python
from functools import lru_cache
from typing import Dict, Optional

def fibonacci(n: int, _cache: Optional[Dict[int, int]] = None) -> int:
    """
    Calculate the nth Fibonacci number efficiently.
    
    Uses memoization to cache results and avoid redundant calculations.
    Time complexity: O(n) for first call, O(1) for cached values.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
        _cache: Internal cache (do not use directly)
        
    Returns:
        The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
        
    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(10)
        55
        >>> fibonacci(50)
        12586269025
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    
    if _cache is None:
        _cache = {}
    
    if n in _cache:
        return _cache[n]
    
    if n <= 1:
        result = n
    else:
        result = fibonacci(n - 1, _cache) + fibonacci(n - 2, _cache)
    
    _cache[n] = result
    return result


# Alternative implementation using Python's built-in LRU cache
@lru_cache(maxsize=128)
def fibonacci_lru(n: int) -> int:
    """
    Calculate the nth Fibonacci number using LRU cache decorator.
    
    This is a cleaner approach when you don't need manual cache control.
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    return fibonacci_lru(n - 1) + fibonacci_lru(n - 2)


# Unit tests
def test_fibonacci():
    """Test fibonacci function with various inputs."""
    # Test base cases
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    
    # Test known values
    assert fibonacci(10) == 55
    assert fibonacci(20) == 6765
    
    # Test negative input
    try:
        fibonacci(-1)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    # Test cache effectiveness
    import time
    start = time.time()
    fibonacci(35)  # First call
    first_duration = time.time() - start
    
    start = time.time()
    fibonacci(35)  # Cached call
    cached_duration = time.time() - start
    
    assert cached_duration < first_duration * 0.1  # Should be much faster
    
    print("All tests passed!")

if __name__ == "__main__":
    test_fibonacci()
```

### Human Review

**Decision**: Approved  
**Feedback**: "Excellent implementation with both manual and decorator approaches"  
**Satisfaction**: High  
**Review Duration**: 45 seconds

### Context Manager Updates
- Pattern confidence increased: "memoization for recursion" (+0.02)
- New pattern recorded: "lru_cache vs manual caching comparison"
- Success logged for similar requests

---

## Example 2: Fix SQL Injection Vulnerability

### Request
"Fix this SQL query to prevent injection: `query = f\"SELECT * FROM users WHERE name = '{username}'\"`"

### Execution Flow

#### 1. IDLE → REQUEST_RECEIVED (0.1s)
```
Request type: Security fix
Priority: High
Context needed: SQL injection patterns
```

#### 2. REQUEST_RECEIVED → CONTEXT_SEARCH (1.8s)
```
Found critical security patterns:
1. [0.98] SQL parameterized queries
2. [0.96] Common injection prevention
3. [0.93] Python database security
4. [0.90] Query builder patterns
```

#### 3. CONTEXT_SEARCH → EXECUTING (3.2s)
```
Applying security patterns:
✓ Parameterized query conversion
✓ Input validation addition
✓ Error handling
✓ Security comments
```

### Generated Output

```python
import sqlite3
from typing import List, Optional, Dict, Any

def get_user_by_name_safe(username: str, connection: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Safely retrieve user by username using parameterized query.
    
    This prevents SQL injection by using parameter substitution
    instead of string formatting.
    
    Args:
        username: The username to search for
        connection: Active database connection
        
    Returns:
        User data as dictionary or None if not found
        
    Security:
        - Uses parameterized queries to prevent SQL injection
        - Validates input before query execution
        - Returns sanitized data only
    """
    # Input validation
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")
    
    # SECURE: Using parameterized query with ? placeholder
    query = "SELECT * FROM users WHERE name = ?"
    
    try:
        cursor = connection.cursor()
        # Pass username as parameter, not string concatenation
        cursor.execute(query, (username,))
        
        row = cursor.fetchone()
        if row:
            # Convert to dictionary for easier handling
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
        
    except sqlite3.Error as e:
        # Log error securely (don't expose query details)
        print(f"Database error occurred: {type(e).__name__}")
        raise
    finally:
        cursor.close()


# Additional security utilities
def validate_username(username: str) -> bool:
    """
    Validate username against security rules.
    
    Rules:
    - 3-50 characters
    - Alphanumeric, underscore, hyphen only
    - Cannot start with number
    """
    import re
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username))


# Example usage with connection pooling
def get_user_with_validation(username: str, db_path: str) -> Optional[Dict[str, Any]]:
    """Complete example with validation and connection handling."""
    if not validate_username(username):
        raise ValueError(f"Invalid username format: {username}")
    
    with sqlite3.connect(db_path) as conn:
        return get_user_by_name_safe(username, conn)


# UNSAFE - Original code for comparison
def get_user_unsafe(username: str, connection: sqlite3.Connection):
    """DO NOT USE - Vulnerable to SQL injection!"""
    # VULNERABLE: String formatting allows injection
    query = f"SELECT * FROM users WHERE name = '{username}'"
    # Attacker could input: ' OR '1'='1' --
    # Resulting in: SELECT * FROM users WHERE name = '' OR '1'='1' --'
    cursor = connection.cursor()
    cursor.execute(query)  # DANGEROUS!
    return cursor.fetchall()
```

### Human Review

**Decision**: Approved  
**Feedback**: "Comprehensive fix with good security practices"  
**Note**: "Consider adding rate limiting for production"

---

## Example 3: Write Unit Tests

### Request
"Write unit tests for this shopping cart class that handles adding, removing items and calculating total"

### Context Found
- pytest patterns
- mock usage examples  
- edge case testing strategies
- fixture best practices

### Generated Output

```python
import pytest
from decimal import Decimal
from typing import Dict, List
from dataclasses import dataclass
from unittest.mock import Mock, patch

# Assuming this is the class to test
@dataclass
class CartItem:
    product_id: str
    name: str
    price: Decimal
    quantity: int

class ShoppingCart:
    """Shopping cart implementation to be tested."""
    def __init__(self):
        self.items: Dict[str, CartItem] = {}
    
    def add_item(self, product_id: str, name: str, price: Decimal, quantity: int = 1):
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            self.items[product_id] = CartItem(product_id, name, price, quantity)
    
    def remove_item(self, product_id: str, quantity: int = None):
        if product_id not in self.items:
            raise ValueError(f"Product {product_id} not in cart")
        
        if quantity is None:
            del self.items[product_id]
        else:
            self.items[product_id].quantity -= quantity
            if self.items[product_id].quantity <= 0:
                del self.items[product_id]
    
    def calculate_total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items.values())


# Comprehensive test suite
class TestShoppingCart:
    """Test suite for ShoppingCart functionality."""
    
    @pytest.fixture
    def cart(self):
        """Provide a fresh cart for each test."""
        return ShoppingCart()
    
    @pytest.fixture
    def sample_items(self):
        """Common test items."""
        return [
            ("PROD001", "Laptop", Decimal("999.99"), 1),
            ("PROD002", "Mouse", Decimal("29.99"), 2),
            ("PROD003", "Keyboard", Decimal("79.99"), 1)
        ]
    
    # Adding items tests
    def test_add_single_item(self, cart):
        """Test adding a single item to empty cart."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"))
        
        assert len(cart.items) == 1
        assert cart.items["PROD001"].name == "Laptop"
        assert cart.items["PROD001"].quantity == 1
        assert cart.items["PROD001"].price == Decimal("999.99")
    
    def test_add_multiple_different_items(self, cart, sample_items):
        """Test adding multiple different items."""
        for product_id, name, price, quantity in sample_items:
            cart.add_item(product_id, name, price, quantity)
        
        assert len(cart.items) == 3
        assert cart.items["PROD002"].quantity == 2
    
    def test_add_same_item_increases_quantity(self, cart):
        """Test that adding same item increases quantity."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 1)
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        
        assert cart.items["PROD001"].quantity == 3
        assert len(cart.items) == 1
    
    def test_add_item_with_zero_quantity(self, cart):
        """Test edge case of zero quantity."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 0)
        assert cart.items["PROD001"].quantity == 0
    
    # Removing items tests
    def test_remove_entire_item(self, cart):
        """Test removing entire item from cart."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        cart.remove_item("PROD001")
        
        assert "PROD001" not in cart.items
        assert len(cart.items) == 0
    
    def test_remove_partial_quantity(self, cart):
        """Test removing partial quantity."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 5)
        cart.remove_item("PROD001", 2)
        
        assert cart.items["PROD001"].quantity == 3
    
    def test_remove_all_quantity_removes_item(self, cart):
        """Test that removing all quantity removes item."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        cart.remove_item("PROD001", 2)
        
        assert "PROD001" not in cart.items
    
    def test_remove_nonexistent_item_raises_error(self, cart):
        """Test removing non-existent item raises ValueError."""
        with pytest.raises(ValueError, match="Product INVALID not in cart"):
            cart.remove_item("INVALID")
    
    def test_remove_more_than_available_removes_item(self, cart):
        """Test removing more than available quantity."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        cart.remove_item("PROD001", 5)
        
        assert "PROD001" not in cart.items
    
    # Calculate total tests
    def test_calculate_total_empty_cart(self, cart):
        """Test total of empty cart is zero."""
        assert cart.calculate_total() == Decimal("0")
    
    def test_calculate_total_single_item(self, cart):
        """Test total with single item."""
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        
        expected = Decimal("999.99") * 2
        assert cart.calculate_total() == expected
    
    def test_calculate_total_multiple_items(self, cart, sample_items):
        """Test total with multiple items."""
        for product_id, name, price, quantity in sample_items:
            cart.add_item(product_id, name, price, quantity)
        
        expected = (Decimal("999.99") * 1 + 
                   Decimal("29.99") * 2 + 
                   Decimal("79.99") * 1)
        assert cart.calculate_total() == expected
    
    def test_calculate_total_precision(self, cart):
        """Test decimal precision is maintained."""
        cart.add_item("PROD001", "Item1", Decimal("0.01"), 3)
        cart.add_item("PROD002", "Item2", Decimal("0.02"), 1)
        
        assert cart.calculate_total() == Decimal("0.05")
    
    # Integration tests
    def test_add_remove_total_workflow(self, cart):
        """Test complete workflow of add, remove, and total."""
        # Add items
        cart.add_item("PROD001", "Laptop", Decimal("999.99"), 2)
        cart.add_item("PROD002", "Mouse", Decimal("29.99"), 3)
        
        # Check initial total
        assert cart.calculate_total() == Decimal("999.99") * 2 + Decimal("29.99") * 3
        
        # Remove some items
        cart.remove_item("PROD001", 1)
        cart.remove_item("PROD002", 1)
        
        # Check updated total
        assert cart.calculate_total() == Decimal("999.99") + Decimal("29.99") * 2
    
    # Edge cases and error conditions
    def test_negative_price_handling(self, cart):
        """Test handling of negative prices (if allowed)."""
        cart.add_item("DISCOUNT", "Discount", Decimal("-10.00"), 1)
        cart.add_item("PROD001", "Item", Decimal("50.00"), 1)
        
        assert cart.calculate_total() == Decimal("40.00")
    
    @pytest.mark.parametrize("price,quantity,expected", [
        (Decimal("10.00"), 0, Decimal("0.00")),
        (Decimal("0.00"), 10, Decimal("0.00")),
        (Decimal("10.99"), 3, Decimal("32.97")),
    ])
    def test_various_price_quantity_combinations(self, cart, price, quantity, expected):
        """Test various price and quantity combinations."""
        cart.add_item("TEST", "Test Item", price, quantity)
        assert cart.calculate_total() == expected

# Run tests with: pytest test_shopping_cart.py -v
```

### Review Result
**Decision**: Approved  
**Feedback**: "Comprehensive test coverage with good edge cases"  
**Suggestion**: "Consider adding performance tests for large carts"

---

## Example 4: Quick Documentation Fix

### Request
"Add a proper docstring to this FastAPI endpoint that returns user profile"

### Execution Time
Total: 12.3 seconds

### Generated Output

```python
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    """User profile response model."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int, include_inactive: bool = False):
    """
    Retrieve a user profile by ID.
    
    This endpoint fetches user profile information from the database
    and returns it in a structured format. By default, only active
    users are returned unless specifically requested otherwise.
    
    Args:
        user_id: The unique identifier of the user to retrieve
        include_inactive: Whether to include inactive users in the search
        
    Returns:
        UserProfile: Complete user profile information including:
            - id: User's unique identifier
            - username: User's login name  
            - email: User's email address
            - full_name: User's full name (optional)
            - is_active: Whether the user account is active
            
    Raises:
        HTTPException: 
            - 404: User not found
            - 403: Attempting to access inactive user without permission
            
    Examples:
        GET /users/123
        Response: {
            "id": 123,
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true
        }
        
        GET /users/456?include_inactive=true
        Response: {
            "id": 456,
            "username": "janedoe",
            "email": "jane@example.com",
            "full_name": "Jane Doe", 
            "is_active": false
        }
        
    Security:
        Requires authentication token in header.
        Only admins can view inactive users.
    """
    # Implementation here
    pass
```

---

## Common Patterns Observed

### Success Patterns
1. **Clear, specific requests** → Higher quality output
2. **Context reuse** → Faster execution (2-3x speedup)
3. **Iterative refinement** → Better final results
4. **Pattern learning** → Improved suggestions over time

### Failure Patterns
1. **Vague requests** → Poor results requiring clarification
2. **Missing context** → Generic solutions
3. **Unrealistic scope** → Timeouts or partial results
4. **Conflicting requirements** → Confused output

### Performance Metrics

| Request Type | Avg Time | Success Rate | Context Hit Rate |
|-------------|----------|--------------|------------------|
| Code Generation | 8.2s | 85% | 73% |
| Bug Fixes | 6.5s | 91% | 82% |
| Documentation | 5.1s | 94% | 67% |
| Refactoring | 12.4s | 78% | 71% |
| Test Writing | 9.7s | 88% | 79% |

---

*These examples demonstrate the Swiss Army Knife workflow's versatility and effectiveness for rapid development tasks.*