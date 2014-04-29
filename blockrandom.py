import multiprocessing
import Queue
from random import SystemRandom
from struct import unpack

from entropy_collector import HashCollectorDaemon
from math_utils import murmur3_32, _rshift

_queue = multiprocessing.Queue(5000)
_spare_queue = multiprocessing.Queue(5000)
_url = "http://blockchain.info/unconfirmed-transactions?format=json"
_sysrandom = SystemRandom()

stream_entropy_daemon = HashCollectorDaemon(
    _url, _queue, _spare_queue, _sysrandom
)

stream_entropy_daemon.daemon = True
stream_entropy_daemon.start()


def randbytes(num_bytes):
    """
    Returns a bytearray of random bytes from the cache.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    if num_bytes < 1:
        raise ValueError("Number of bytes must be >= 1")

    bytes = []
    while len(bytes) < num_bytes:
        bytes.append(_queue.get())
    return bytearray(bytes)


def u_randbytes(num_bytes):
    """
    Returns a bytearray of random bytes from the cache.
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    if num_bytes < 1:
        raise ValueError("Number of bytes must be >= 1")

    bytes = []
    block = []
    while len(bytes) < num_bytes:
        try:
            block.append(_queue.get_nowait())
        except Queue.Empty:
            try:
                block = [_spare_queue.get_nowait() for i in range(4)]
                block = list(murmur3_32(bytearray(block)))
            except Queue.Empty:
                stream_entropy_daemon._use_cpu_entropy()
        if len(block) == 4:
            for byte in block:
                bytes.append(byte)
                try:
                    _spare_queue.put_nowait(byte)
                except Queue.Full:
                    pass
            block = []
    return bytearray(bytes)[:num_bytes]


def randbool():
    """
    Returns a random boolean value.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    return _next(1) == 0


def u_randbool():
    """
    Returns a random boolean value.
    If no entropy is available, previous entropy will be re-used.
    """
    return _u_next(1) == 0


def _next(bits):
    """
    Return the specified number of random bits (0-32) as an int.
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    """
    return int(_rshift(unpack(">q", randbytes(8))[0], 48 - bits))


def _u_next(bits):
    """
    Return the specified number of random bits (0-32) as an int.
    If no entropy is available, previous entropy will be re-used.
    """
    return int(_rshift(unpack(">q", u_randbytes(8))[0], 48 - bits))


def randint(min_n, max_n):
    """
    Returns a random 32-bit precision in between min_n (inclusive) and max_n
    (exclusive).
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    if not (type(min_n) == type(max_n) == int):
        raise TypeError("min and max must be of type int")

    int_range = max_n - min_n
    if ((int_range & -int_range) == int_range):
        # if int_range is a power of 2
        return int((int_range * long(_next(31))) >> 31) + min_n
    else:
        bits = _next(31)
        next_int = bits % int_range
        while (bits - int_range + (int_range-1)) < 0:
            bits = _next(31)
            next_int = bits % int_range
    return next_int + min_n


def u_randint(min_n, max_n):
    """
    Returns a random 32-bit precision in between min_n (inclusive) and max_n
    (exclusive).
    If no entropy is available, previous entropy will be re-used.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    if not (type(min_n) == type(max_n) == int):
        raise TypeError("min and max must be of type int")

    int_range = max_n - min_n
    if ((int_range & -int_range) == int_range):
        # if int_range is a power of 2
        return int((int_range * long(_u_next(31))) >> 31) + min_n
    else:
        bits = _u_next(31)
        next_int = bits % int_range
        while (bits - next_int + (int_range-1)) < 0:
            bits = _u_next(31)
            next_int = bits % int_range
        return next_int + min_n


def random():
    """
    Returns a random 32-bit precision float.
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    """
    return _next(24) / float(1 << 24)


def u_random():
    """
    Returns a random 32-bit precision float.
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    """
    return _u_next(24) / float(1 << 24)


def uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and max_n
    (exclusive).
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    return random() * (max_n - min_n) + min_n


def u_uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and max_n
    (exclusive).
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    return u_random() * (max_n - min_n) + min_n


def shuffle(iterable):
    """
    Shuffle an iterable in place (i.e., the original is mutated).
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    Uses the Fisher-Yates algorithm.
    """
    length = len(iterable)
    for i in range(length):
        j = randint(i, length)
        iterable[i], iterable[j] = iterable[j], iterable[i]


def u_shuffle(iterable):
    """
    Shuffle an iterable in place (i.e., the original is mutated).
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    Uses the Fisher-Yates algorithm.
    """
    length = len(iterable)
    for i in range(length):
        j = u_randint(i, length)
        iterable[i], iterable[j] = iterable[j], iterable[i]


def shuffled(iterable):
    """
    Returns a randomly shuffled list of elements given an iterable (i.e. the
    original iterable is not mutated).
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    Uses the Fisher-Yates algorithm.
    """
    copy = iterable[:]
    length = len(copy)
    for i in range(length):
        j = randint(i, length)
        copy[i], copy[j] = copy[j], copy[i]
    return copy


def u_shuffled(iterable):
    """
    Returns a randomly shuffled list of elements given an iterable (i.e. the
    original iterable is not mutated).
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    Uses the Fisher-Yates algorithm.
    """
    copy = iterable[:]
    length = len(copy)
    for i in range(length):
        j = u_randint(i, length)
        copy[i], copy[j] = copy[j], copy[i]
    return copy


def choice(iterable):
    """
    Returns a randomly chosen element from an iterable.
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    """
    return iterable[randint(0, len(iterable))]


def u_choice(iterable):
    """
    Returns a randomly chosen element from an iterable.
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    """
    return iterable[u_randint(0, len(iterable))]


def sample(iterable, n):
    """
    Returns a randomly chosen sample of size n from an iterable.
    If no entropy is available, the current thread will block until more is
    retrieved from the blockchain.
    Uses the reservoir sampling algorithm.
    """
    count = 0
    reservoir = []
    rand_int = 0
    for item in iterable:
        count += 1
        if count <= n:
            reservoir.append(item)
        else:
            rand_int = randint(0, count)
            if rand_int < n:
                reservoir[rand_int] = item
    return reservoir


def u_sample(iterable, n):
    """
    Returns a randomly chosen sample of size n from an iterable.
    Like /dev/urandom, previously captured entropy is re-used so that the
    thread will not block.
    Uses the reservoir sampling algorithm.
    """
    count = 0
    reservoir = []
    rand_int = 0
    for item in iterable:
        count += 1
        if count <= n:
            reservoir.append(item)
        else:
            rand_int = u_randint(0, count)
            if rand_int < n:
                reservoir[rand_int] = item
    return reservoir
