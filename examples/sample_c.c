/**
 * Sample C code for testing abstraction tracking.
 */

#include <stdio.h>
#include <assert.h>

int calculate(int x);
int helper(int x);
void display(int value);

int main() {
    /*
     * Entry point
     * 
     * Preconditions: none
     * Postconditions: returns 0 on success
     */
    int result = calculate(10);
    display(result);
    
    assert(result > 0);
    return 0;
}

int calculate(int x) {
    /*
     * Calculate result
     * 
     * Preconditions: x > 0
     * Postconditions: returns x * 2
     */
    assert(x > 0);
    
    int temp = helper(x);
    int result = temp * 2;
    
    assert(result > x);
    return result;
}

int helper(int x) {
    /*
     * Helper function
     * 
     * Preconditions: x is valid integer
     * Postconditions: returns x + 5
     */
    int result = x + 5;
    
    assert(result > x);
    return result;
}

void display(int value) {
    /*
     * Display value
     * 
     * Preconditions: value is valid
     * Postconditions: value printed
     */
    printf("Result: %d\n", value);
    assert(value >= 0);
}
