from flask import Flask
import os
import random

app = Flask(__name__)

def fibonacci(n):
    if n<= 0:
        print("Incorrect input")
    # First Fibonacci number is 0
    elif n == 1:
        return 0
    # Second Fibonacci number is 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n-1)+fibonacci(n-2)

@app.route('/')
def get_fibo():
    num = random.randint(10,35)
    return f"The {num} Fibonacci number is {fibonacci(num)}"


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)