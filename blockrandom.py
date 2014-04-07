import multiprocessing, Queue, sys, urllib2
from murmur3 import murmur3_bytes, iterative_murmur3, murmur3_32
from time import sleep, time
from threading import RLock
from json import loads
from collections import deque
from operator import add


_queue = multiprocessing.Queue(5000)
_spare_queue = multiprocessing.Queue(5000)
_url = "https://blockchain.info/unconfirmed-transactions?format=json"

_cache = RLock()
_cache.most_recent = 0

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
                    json = loads(response.read())
                    return json
            except (urllib2.HTTPError, urllib2.URLError):
                sleep(11) # as per blockchain.info API policy
            tries_left -= 1


def fill_cache():
    """
    Fill the cache with entropy from recent transactions.
    """
    tries = 8
    while True:
        if tries <= 0:
            raise BlockchainError("Cannot find new transactions")
        else:
            transaction_json = get_unconfirmed_transactions()['txs']
            if len(transaction_json) == 0 or \
                    transaction_json[0]['time'] <= _cache.most_recent:
                tries -= 1
                sleep(11) # as per blockchain.info API policy
            else:
                break
    
    _cache.acquire()
    try:
        transaction_json = filter(lambda x: x > _cache.most_recent, transaction_json)
        _cache.most_recent = max((t['time'] for t in transaction_json))
    except Exception as e:
        sys.stderr.write(e)
    finally:
        _cache.release()
    
    hex_hashes = reduce(add, (t['hash'] for t in transaction_json))
    bytes = bytearray.fromhex(hex_hashes)

    for byte in bytes[::-1]:
        _queue.put(byte)
        _spare_queue.put(byte)


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
            fill_cache()
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
        if len(block) == 4:
            for byte in murmur3_32(bytearray(block)):
                bytes.append(byte)
                try:
                    _spare_queue.put_nowait(byte)
                except Queue.Full:
                    continue
            block = []
        try:
            block.append(_spare_queue.get_nowait())
        except Queue.Empty:
            # temporary hack
            try:
                for byte in murmur3_32(time()):
                    _spare_queue.put_nowait(byte)
            except Queue.Full:
                pass
    return bytearray(bytes)


def randbool():
    """
    Returns a random boolean value.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    while True:
        try:
            return (_queue.get_nowait() % 2) == 0
        except Queue.Empty:
            fill_cache()


def u_randbool():
    """
    Returns a random boolean value.
    If no entropy is available, previous entropy will be re-used.
    """
    # coming soon
    pass
    

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
    # coming soon
    pass


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
    # coming soon
    pass
    

def random():
    """
    Returns a random 32-bit precision float.
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    # coming soon
    pass


def u_random():
    """
    Returns a random 32-bit precision float.
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    # coming soon
    pass
    

def uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and
    max_n (exclusive).
    If no entropy is available, the current thread will block until more
    is retrieved from the blockchain.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    # coming soon
    pass


def u_uniform(min_n, max_n):
    """
    Returns a random 32-bit precision float between min_n (exclusive) and
    max_n (exclusive).
    Like /dev/urandom, previously captured entropy is re-used so that
    the thread will not block.
    """
    if min_n >= max_n:
        raise ValueError("min cannot be greater than max")
    # coming soon
    pass

fill_cache()
