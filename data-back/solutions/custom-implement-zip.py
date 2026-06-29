"""A from-scratch reimplementation of the built-in zip().

Works on any iterables (including infinite/streaming ones) because it drives
them through iterators and produces tuples lazily via `yield`.
"""


def my_zip(*iterables, strict=False):
    if not iterables:
        return
    iterators = [iter(it) for it in iterables]
    while True:
        result = []
        for i, it in enumerate(iterators):
            try:
                result.append(next(it))
            except StopIteration:
                if not strict:
                    return
                # In strict mode a clean end is only legal when the FIRST
                # iterator is the one that stopped *and* every other iterator
                # is also exhausted. Anything else is a length mismatch.
                if i == 0:
                    for j, other in enumerate(iterators[1:], start=1):
                        try:
                            next(other)
                        except StopIteration:
                            continue
                        raise ValueError(
                            f"my_zip() argument {j + 1} is longer than argument 1"
                        )
                    return
                raise ValueError(
                    f"my_zip() argument {i + 1} is shorter than argument 1"
                )
        yield tuple(result)


if __name__ == "__main__":
    assert list(my_zip("ABCD", "xy")) == [("A", "x"), ("B", "y")]
    assert list(my_zip(range(3), range(5), range(2))) == [(0, 0, 0), (1, 1, 1)]
    assert list(my_zip()) == []
    assert list(my_zip([1, 2, 3])) == [(1,), (2,), (3,)]
    assert list(my_zip([1, 2], [3, 4], strict=True)) == [(1, 3), (2, 4)]

    for bad in ([1, 2, 3], [4, 5]), ([1], [2, 3]):
        try:
            list(my_zip(*bad, strict=True))
        except ValueError as e:
            print("strict raised as expected:", e)
        else:
            raise AssertionError("expected ValueError in strict mode")

    print("all checks passed")
