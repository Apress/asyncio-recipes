async def complicated(a, b, c):
    """
    >>> import asyncio
    >>> asyncio.run(complicated(5,None,None))
    True
    >>> asyncio.run(complicated(None,None,None))
    Traceback (most recent call last):
        ...
    ValueError: This value: None is not an int or larger than 4
    >>> asyncio.run(complicated(None,"This","will be printed out"))
    This will be printed out

    :param a: This parameter controls the return value
    :param b:
    :param c:
    :return:
    """
    if isinstance(a, int) and a > 4:
        return True
    elif b and c:
        print(b, c)
    else:
        raise ValueError(f"This value: {a} is not an int or larger than 4")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
