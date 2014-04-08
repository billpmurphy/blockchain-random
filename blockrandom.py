import multiprocessing, threading, Queue, sys, urllib2
from murmur3 import murmur3_bytes, iterative_murmur3, murmur3_32
from time import sleep, time
from json import loads
from collections import deque
from operator import add
from random import SystemRandom
from struct import unpack


_queue = multiprocessing.Queue(5000)
_spare_queue = multiprocessing.Queue(5000)
_url = "https://blockchain.info/unconfirmed-transactions?format=json"

_cache = threading.RLock()
_cache.most_recent = 0

_sysrandom = SystemRandom() # only use in the most dire circumstances

class BlockchainError(Exception):
    pass


def get_unconfirmed_transactions(url=_url):
    """
    Fetches the list of unconfirmed transactions from blockchain.info.
    """
    tries_left = 8
    while True:
        if tries_left <= 0:
            raise BlockchainError("Cannot connect to blockchain.info")
        else:
            try:
                response = urllib2.urlopen(url)
                if response.code == 200:
                    return loads(response.read())
            except (urllib2.HTTPError, urllib2.URLError):
                sleep(11) # as per blockchain.info API policy
            tries_left -= 1


def fill_cache():
    """
    Fill the cache with entropy from recent transactions.
    """
    _cache.acquire()
    try:
        tries = 8
        while True:
            if tries <= 0:
                raise BlockchainError("Cannot find new transactions")
            else:
                transactions = get_unconfirmed_transactions()['txs']
                if len(transactions) == 0 or \
                        transactions[0]['time'] <= _cache.most_recent:
                    tries -= 1
                    sleep(11) # as per blockchain.info API policy
                else:
                    break
        transactions = filter(lambda x: x > _cache.most_recent, transactions)
        _cache.most_recent = max((t['time'] for t in transactions))
    except Exception as e:
        sys.stderr.write(e)
    finally:
        _cache.release()

    hex_hashes = reduce(add, (t['hash'] for t in transactions))
    bytes = bytearray.fromhex(hex_hashes)

    for byte in bytes[::-1]:
        try:
            _queue.put_nowait(byte)
        except Queue.Full:
            pass
        try:
            _spare_queue.put_nowait(byte)
        except Queue.Full:
            pass


def use_cpu_entropy():
    """
    If, by some freak accident, we have nothing left in the spare cache,
    lean on Python's random.SystemRandom to get some entropy.
    """
    sys.stderr.write("WARNING: Using /dev/urandom.\n")
    try:
        for byte in (_sysrandom.randint(0, 256) for i in range(8)):
            _spare_queue.put_nowait(byte)
    except Queue.Full:
        pass


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
        try:
            bytes.append(_queue.get_nowait())
        except Queue.Empty:
            refill = threading.Thread(target=fill_cache())
            refill.start()
            refill.join()
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
                use_cpu_entropy() # temporary hack
        if len(block) == 4:
            for byte in block:
                bytes.append(byte)
                try:
                    _spare_queue.put_nowait(byte)
                except Queue.Full:
                    continue
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


def _rshift(val, n):
    """
    Python equivalent of unsigned right bitshift operator.
    (Same as (int)((long)val >>> n) in Java.)
    """
    return (val % 0x1000000000000) >> n


def _next(bits):
    """
    Return the specified number of random bits (0-32) as an int.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    return int(_rshift(unpack(">q",randbytes(8))[0], 48 - bits))


def _u_next(bits):
    """
    Return the specified number of random bits (0-32) as an int.
    If no entropy is available, previous entropy will be re-used.
    """
    return int(_rshift(unpack(">q",u_randbytes(8))[0], 48 - bits))


def randint(min_n, max_n):
    """
    Returns a random 32-bit precision in between min_n (inclusive) and
    max_n (exclusive).
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
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
    Returns a random 32-bit precision in between min_n (inclusive) and
    max_n (exclusive).
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
            bits = u_next(31)
            next_int = bits % int_range
        return next_int + min_n


def random():
    """
    Returns a random 32-bit precision float.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    return _next(24) / float(1 << 24)


def u_random():
    """
    Returns a random 32-bit precision float.
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    return _u_next(24) / float(1 << 24)


def uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and
    max_n (exclusive).
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    return random() * (min_n - max_n) + min_n


def u_uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and
    max_n (exclusive).
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    return u_random() * (min_n - max_n) + min_n


def shuffle(iterable):
    """
    Shuffle an iterable in place (i.e., the original is mutated).
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    # Fisher-Yates algorithm
    length = len(iterable)
    for i in range(length):
        j = randint(i, length)
        iterable[i], iterable[j] = iterable[j], iterable[i]


def u_shuffle(iterable):
    """
    Shuffle an iterable in place (i.e., the original is mutated).
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    # Fisher-Yates algorithm
    length = len(iterable)
    for i in range(length):
        j = u_randint(i, length)
        iterable[i], iterable[j] = iterable[j], iterable[i]


def shuffled(iterable):
    """
    Returns a randomly shuffled list of elements given an iterable
    (i.e. the original iterable is not mutated).
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    # Fisher-Yates algorithm
    copy = iterable[:]
    length = len(copy)
    for i in range(length):
        j = randint(i, length)
        copy[i], copy[j] = copy[j], copy[i]
    return copy


def u_shuffled(iterable):
    """
    Returns a randomly shuffled list of elements given an iterable
    (i.e. the original iterable is not mutated).
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    # Fisher-Yates algorithm
    copy = iterable[:]
    length = len(copy)
    for i in range(length):
        j = u_randint(i, length)
        copy[i], copy[j] = copy[j], copy[i]
    return copy


def choice(iterable):
    """
    Returns a randomly chosen element from an iterable.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    return iterable[randint(0, len(iterable))]


def u_choice(iterable):
    """
    Returns a randomly chosen element from an iterable.
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    return iterable[u_randint(0, len(iterable))]


