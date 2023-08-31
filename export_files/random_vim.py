import random
import string

def generate_random_alphanumeric(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

random_numbers = [generate_random_alphanumeric(19) for _ in range(6)]
print(random_numbers)
