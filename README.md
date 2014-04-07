Entropy from bitcoin transactions
=================================

Are you trying to use true randomness in your application, but don't want to use `/dev/random` or [random.org](https://random.org) because they are "too mainstream" or "not edgy enough" for your project? Fear not! With `blockrandom.py`, you can get entropy straight from unconfirmed bitcoin transactions! Now you can develop applications in style, safe with the knowledge that you have the hippest source of true randomness in town.

### How to use it ###

You can use `blockrandom.py` just like Python's standard library `random` module.

```python
>>> import blockrandom
>>> blockrandom.randbytes(5)
bytearray(b'\xff\xdcb\x9c\xee')

>>> blockrandom.randbool()
True

>>> blockrandom.randint(0, 100)
43
````

If you want a non-blocking random generator that will recycle previously collected entropy, similar to `/dev/urandom`, you can use the following:

```python
>>> blockrandom.u_randbytes(5)
bytearray(b'\xe5\x84Y\x87a')

>>> blockrandom.u_randbool()
False

>>> blockrandom.u_randint(0, 100)
22
```

More features (like `random()` and `uniform()`) are coming soon!

### How it works ###

Unconfirmed transaction hashes are queried from [blockchain.info](https://blockchain.info). If we need to recycle previous entropy, we use the 32-bit MurmurHash3 function.

More explanation of this coming soon, for now see the `randomness_testing.py` file and the `experiments` directory, which shows the results of the experiments enumerated in `randomness_testing.py`.
