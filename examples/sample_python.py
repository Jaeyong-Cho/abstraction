"""Sample Python code for testing abstraction tracking."""


def main():
    """
    Entry point of the program.
    
    Preconditions: none
    Postconditions: program executes successfully, returns 0
    """
    result = process_data(10)
    output = format_result(result)
    display_output(output)
    
    assert result > 0, "Result must be positive"
    assert isinstance(output, str), "Output must be string"
    
    return 0


def process_data(value):
    """
    Process input value.
    
    Preconditions: value is positive integer
    Postconditions: returns processed value (doubled)
    """
    assert value > 0, "Value must be positive"
    
    intermediate = calculate_intermediate(value)
    result = apply_transformation(intermediate)
    
    assert result > value, "Result must be greater than input"
    return result


def calculate_intermediate(value):
    """
    Calculate intermediate value.
    
    Preconditions: value is positive
    Postconditions: returns value plus 5
    """
    assert value > 0, "Value must be positive"
    
    result = value + 5
    
    assert result > value, "Result must be greater"
    return result


def apply_transformation(value):
    """
    Apply transformation to value.
    
    Preconditions: value is numeric
    Postconditions: returns value multiplied by 2
    """
    assert isinstance(value, (int, float)), "Value must be numeric"
    
    result = value * 2
    
    assert result >= 0, "Result must be non-negative"
    return result


def format_result(value):
    """
    Format result as string.
    
    Preconditions: value is numeric
    Postconditions: returns formatted string representation
    """
    assert isinstance(value, (int, float)), "Value must be numeric"
    
    formatted = f"Result: {value}"
    
    assert isinstance(formatted, str), "Must return string"
    return formatted


def display_output(message):
    """
    Display output message.
    
    Preconditions: message is string
    Postconditions: message printed to stdout
    """
    assert isinstance(message, str), "Message must be string"
    
    print(message)
    
    assert len(message) > 0, "Message must not be empty"


if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
