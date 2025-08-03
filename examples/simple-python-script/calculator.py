"""
Simple Calculator Implementation
A basic calculator with arithmetic operations and error handling.
"""

class Calculator:
    """A simple calculator class with basic arithmetic operations."""
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base ** exponent

def main():
    """Simple CLI interface for the calculator."""
    calc = Calculator()
    
    print("Simple Calculator")
    print("Available operations: +, -, *, /, ^")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\nEnter calculation (e.g., 5 + 3): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # Parse input
            parts = user_input.split()
            if len(parts) != 3:
                print("Invalid format. Use: number operator number")
                continue
            
            a, operator, b = parts
            a, b = float(a), float(b)
            
            # Perform calculation
            if operator == '+':
                result = calc.add(a, b)
            elif operator == '-':
                result = calc.subtract(a, b)
            elif operator == '*':
                result = calc.multiply(a, b)
            elif operator == '/':
                result = calc.divide(a, b)
            elif operator == '^':
                result = calc.power(a, b)
            else:
                print("Unsupported operator. Use: +, -, *, /, ^")
                continue
            
            print(f"Result: {result}")
            
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()