from array import array
from math import log
from operator import add


############ Utilities for Handling Bytearrays ############
def _rshift(val, n):
    """
    Python equivalent of unsigned right bitshift operator.
    (Same as (int)((long)val >>> n) in Java.)
    """
    return (val % 0x1000000000000) >> n


def entropy(bytes):
    """
    Calculate the Shannon entropy of a byte array or a list of
    integers that represents a bytearray.
    """
    byte_ints = array("i", bytes)

    frequencies = [0] * 256
    for byte in byte_ints:
        frequencies[byte] += 1

    entropy = 0.0
    num_bytes = len(byte_ints)
    for f in frequencies:
        if f > 0:
            freq = float(f) / num_bytes
            entropy = entropy + freq * log(freq, 2)
    return -entropy


def save_bytes(bytes, filename):
    """
    Save binary data to file.
    """
    with open(filename, "wb") as f:
        f.write(str(bytes))


def load_bytes(filename):
    """
    Load a binary file.
    """
    with open(filename, "rb") as f:
        bytes = f.read()
    return bytearray(bytes)


############ Assorted MurmurHash3 Utilities ############
def murmur3_32(key, seed=0x0):
    """
    Pure Python implementation of 32-bit murmur3 hashing algorithm. Not
    cryptographically secure, but well-distributed and good enough for our
    purposes.
    """
    assert type(key) is bytearray, "Key must be of type bytearray"
    _len = len(key)

    # mixing constants
    c1 = 0xcc9e2d51
    c2 = 0x1b873593
    r1 = 15
    r2 = 13
    m = 5
    n = 0xe6546b64

    nblocks = _len // 4
    mhash = seed

    # mix into hash, 4 bytes at a time
    for block_start in xrange(0, nblocks * 4, 4):
        k = key[block_start + 3] << 24 | \
            key[block_start + 2] << 16 | \
            key[block_start + 1] << 8 | \
            key[block_start + 0]
        k = (c1 * k) & 0xFFFFFFFF
        k = (k << r1 | k >> (32-r1)) & 0xFFFFFFFF
        k = (c2 * k) & 0xFFFFFFFF
        mhash ^= k
        mhash = (mhash << r2 | mhash >> (32-r2)) & 0xFFFFFFFF
        mhash = (mhash * m + n) & 0xFFFFFFFF

    # make sure last few bytes are mixed (no endian swapping)
    remaining_bytes_index = (_len // 4) * 4
    num_remaining_bytes = _len & 3
    k = 0

    if num_remaining_bytes == 3:
        k ^= key[remaining_bytes_index + 2] << 16
        k ^= key[remaining_bytes_index + 1] << 8
        k ^= key[remaining_bytes_index + 0]
        k = (k * c1) & 0xFFFFFFFF
        k = (k << 16 | k >> 16) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        mhash ^= k
    elif num_remaining_bytes == 2:
        k ^= key[remaining_bytes_index + 1] << 8
        k ^= key[remaining_bytes_index + 0]
        k = (k * c1) & 0xFFFFFFFF
        k = (k << 16 | k >> 16) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        mhash ^= k
    elif num_remaining_bytes == 1:
        k ^= key[remaining_bytes_index + 0]
        k = (k * c1) & 0xFFFFFFFF
        k = (k << 16 | k >> 16) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        mhash ^= k

    # additionl mixing
    mhash ^= _len
    mhash ^= mhash >> 16
    mhash = (mhash * 0x85ebca6b) & 0xFFFFFFFF
    mhash ^= mhash >> 13
    mhash = (mhash * 0xc2b2ae35) & 0xFFFFFFFF
    mhash ^= mhash >> 16

    hex_result = hex(mhash)[2:]
    if hex_result[-1] == "L":
        hex_result = hex_result[:-1]
    if len(hex_result) < 8:
        hex_result = "0" * (8 - len(hex_result)) + hex_result
    return bytearray.fromhex(hex_result)


def iterative_murmur3(key, times=1):
    """
    MurmurHash3 a key and then iteratively re-hash the results some number
    of times.
    """
    key = murmur3_32(key)
    for i in range(times-1):
        key = murmur3_32(key)
    return key


def murmur3_bytes(bytes, times=1):
    """
    Given a bytearray, run MurmurHash3 on each 32-bit chunk and return the
    resulting bytearray.
    """
    if len(bytes) % 4 != 0:
        bytes = bytearray.fromhex("00") * (4 - (len(bytes) % 4)) + bytes
    blocks = (str(bytes)[i:i+4] for i in range(0, len(bytes), 4))
    hashed_blocks = (iterative_murmur3(bytearray(b), times) for b in blocks)
    return reduce(add, hashed_blocks)
