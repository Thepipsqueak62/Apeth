#include <mylibrary/mylibrary.h>
#include <iostream>
#include <vector>

int main() {
    std::cout << "=== Advanced Example ===" << std::endl;

    mylibrary::Calculator calc;

    // Demonstrate all operations
    std::cout << "\n--- Calculator Operations ---" << std::endl;
    std::cout << "10.5 + 5.5 = " << calc.add(10.5, 5.5) << std::endl;
    std::cout << "15.0 - 7.5 = " << calc.subtract(15.0, 7.5) << std::endl;
    std::cout << "3.0 * 4.5 = " << calc.multiply(3.0, 4.5) << std::endl;
    std::cout << "20.0 / 4.0 = " << calc.divide(20.0, 4.0) << std::endl;

    // Demonstrate string utilities
    std::cout << "\n--- String Utilities ---" << std::endl;
    std::string test_string = "  Hello Advanced User  ";
    std::cout << "Original: '" << test_string << "'" << std::endl;

    // Demonstrate error handling
    std::cout << "\n--- Error Handling ---" << std::endl;
    try {
        std::cout << "Attempting division by zero: ";
        std::cout << calc.divide(10.0, 0.0) << std::endl;
    } catch (const std::exception& e) {
        std::cout << "Caught exception: " << e.what() << std::endl;
    }

    // Complex calculation
    std::cout << "\n--- Complex Calculation ---" << std::endl;
    double result = calc.add(
        calc.multiply(2.5, 4.0),
        calc.divide(15.0, 3.0)
    );
    std::cout << "(2.5 * 4.0) + (15.0 / 3.0) = " << result << std::endl;

    std::cout << "\n" << mylibrary::greet("Advanced Developer") << std::endl;
    std::cout << "Library: " << mylibrary::Calculator::version() << std::endl;
    system("pause");

    return 0;
}