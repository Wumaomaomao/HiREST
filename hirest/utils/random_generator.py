import random

def random_gen_integer()-> int:
    """
    Generate a random integer.
    """
    return random.randint(-2147483648, 2147483647)

def random_gen_number()-> float:
    """
    Generate a random number.
    """
    return random.uniform(-1e6, 1e6)

def random_gen_string()-> str:
    """
    Generate a random string.
    """
    length = random.randint(1, 10)
    printable_ascii = ''.join([chr(i) for i in range(32, 127)])
    return ''.join(random.choices(printable_ascii, k=length))

def random_gen_boolean()-> bool:
    """
    Generate a random boolean.
    """
    return random.choice([True, False])