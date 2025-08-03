"""
Unit tests for the Calculator class.
"""

import pytest
from calculator import Calculator


class TestCalculator:
    """Test suite for Calculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calc = Calculator()
    
    def test_add(self):
        """Test addition operation."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0.1, 0.2) == pytest.approx(0.3)
    
    def test_subtract(self):
        """Test subtraction operation."""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 5) == -5
        assert self.calc.subtract(-3, -2) == -1
    
    def test_multiply(self):
        """Test multiplication operation."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 100) == 0
    
    def test_divide(self):
        """Test division operation."""
        assert self.calc.divide(6, 2) == 3
        assert self.calc.divide(5, 2) == 2.5
        assert self.calc.divide(-6, 3) == -2
    
    def test_divide_by_zero(self):
        """Test division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(5, 0)
    
    def test_power(self):
        """Test power operation."""
        assert self.calc.power(2, 3) == 8
        assert self.calc.power(5, 0) == 1
        assert self.calc.power(9, 0.5) == 3
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Large numbers
        assert self.calc.add(1e10, 1e10) == 2e10
        
        # Very small numbers
        assert self.calc.multiply(1e-10, 1e-10) == 1e-20
        
        # Negative operations
        assert self.calc.power(-2, 3) == -8
        assert self.calc.power(-2, 2) == 4