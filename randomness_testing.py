import blockrandom
from math_utils import murmur3_bytes, entropy, load_bytes, save_bytes

def entropy_tests(test_size):
    try:
        print("\n## Test 1: "
            "How good is the blockchain as a source of entropy? ##\n")
        print "Getting %s bytes of transaction hash entropy..." % test_size
        save_bytes(blockrandom.randbytes(test_size), "test_data.bin")
        bytes = load_bytes("test_data.bin")
        print "\tEntropy: %f bits per byte" % entropy(bytes)

        print "\n## Test 2: How good is murmurhash3 as a PRNG function? ##\n"
        print "Running the %s random bytes through MurmurHash3..." % test_size
        hashed_bytes_1000 = murmur3_bytes(bytes, times=1000)
        print "\tEntropy: %f bits per byte" % entropy(hashed_bytes_1000)

        print("\n## Test 3: "
            "Can we use murmur3 to recycle previously captured entropy? ##\n")
        print "Generating %s bytes of psuedorandomness..." % test_size
        save_bytes(blockrandom.u_randbytes(test_size), "test_data2.bin")
        u_bytes = load_bytes("test_data2.bin")
        print "\tEntropy: %f bits per byte" % entropy(u_bytes)
    except KeyboardInterrupt:
        print "Done."

if __name__ == "__main__":
    entropy_tests(1000)
