import blockrandom, math, numpy, pylab
from murmur3 import murmur3_bytes

def entropy(bytes):
    """
    Calculate the Shannon entropy of a byte array.
    """
    byte_ints = numpy.fromstring(str(bytes), dtype = 'uint8')
    num_bytes = len(byte_ints)
    
    frequencies = [0] * 256
    for byte in byte_ints:
        frequencies[byte] += 1
        
    entropy = 0.0
    for f in frequencies:
        if f > 0:
            freq = float(f) / num_bytes
            entropy = entropy + freq * math.log(freq, 2)
    return -entropy
    

def examine(bytes):
    """
    Examine the "randomness" of a given byte array.
    """
    print "Average bits of entropy per byte: %s" % entropy(bytes)
    byte_ints = numpy.fromstring(str(bytes), dtype = 'uint8')
    # histogram
    pylab.figure()
    pylab.hist(byte_ints, bins=256, range=[0,255])
    
    # scatter
    pylab.figure()
    pylab.plot(byte_ints, 'bo', alpha=0.1)
    pylab.show()


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


if __name__ == "__main__":
    ## how good is the blockchain as a source of entropy?
    # get some transaction hash entropy, dump it to file
    save_bytes(blockrandom.randbytes(100000), "test_data.bin")
    bytes = load_bytes("test_data.bin")
    examine(bytes)
    
    ## how good is murmurhash3 as a PRNG?
    # examine the bytes after hashing once with murmur3
    mbytes = murmur3_bytes(bytes)
    examine(mbytes)
    
    # and just to take it a bit further...
    mbytes_1000 = murmur3_bytes(bytes, times=1000)
    examine(mbytes_1000)
    
    ## can we use murmur3 to recycle previously captured entropy?
    # (similar to /dev/urandom)
    save_bytes(blockrandom.u_randbytes(100000), "test_data2.bin")
    u_bytes = load_bytes("test_data2.bin")
    examine(u_bytes)