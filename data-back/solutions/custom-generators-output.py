"""Generators: what does `print(generate_odd_numbers())` print, and how do
you actually consume an infinite generator safely?"""

from itertools import islice


def generate_odd_numbers():
    n = 1
    while True:
        yield n
        n += 2


if __name__ == "__main__":
    # 1) Calling the generator function returns a generator object — the body
    #    has not run yet. This is what the original `print(...)` shows:
    gen = generate_odd_numbers()
    print(repr(gen))            # <generator object generate_odd_numbers at 0x...>

    # 2) Pull values one at a time with next():
    print(next(gen))           # 1
    print(next(gen))           # 3
    print(next(gen))           # 5

    # 3) Take the first N lazily — never list() an infinite generator:
    first_five = list(islice(generate_odd_numbers(), 5))
    print(first_five)          # [1, 3, 5, 7, 9]

    # 4) Iterate with an explicit stop condition:
    for odd in generate_odd_numbers():
        if odd > 9:
            break
        print(odd, end=" ")    # 1 3 5 7 9
    print()
