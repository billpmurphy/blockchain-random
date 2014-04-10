import blockrandom, math, numpy, pylab
from math_utils import murmur3_bytes, entropy, load_bytes, save_bytes


def examine_bytes(bytes):
    """
    Examine the "randomness" of a given byte array.
    """
    print "\tAverage bits of entropy per byte: %s" % entropy(bytes)
    byte_ints = numpy.fromstring(str(bytes), dtype = 'uint8')
    # histogram
    pylab.figure()
    pylab.hist(byte_ints, bins=256, range=[0,255])

    # scatter
    pylab.figure()
    pylab.plot(byte_ints, 'bo', alpha=0.1)
    pylab.show()


def interactive_tests():
    test_size = 100000
    prompt = "Press enter to view graphs (s to skip, q to quit)"

    print "\n## Test 1: How good is the blockchain as a source of entropy? ##\n"
    print "Getting %s bytes of transaction hash entropy..." % test_size
    save_bytes(blockrandom.randbytes(test_size), "test_data.bin")
    bytes = load_bytes("test_data.bin")
    user_input = raw_input(prompt).strip()
    if user_input == "q":
        exit()
    elif user_input == "s":
        pass
    else:
        examine_bytes(bytes)

    print "\n## Test 2: How good is murmurhash3 as a PRNG function? ##\n"
    print "Running the %s random bytes through MurmurHash3..." % test_size
    hashed_bytes_1000 = murmur3_bytes(bytes, times=1000)
    user_input = raw_input(prompt).strip()
    if user_input == "q":
        exit()
    elif user_input == "s":
        pass
    else:
        examine_bytes(hashed_bytes_1000)

    print "\n## Test 3: Can we use murmur3 to recycle previously captured entropy? ##\n"
    print "Generating %s bytes of psuedorandomness..." % test_size
    save_bytes(blockrandom.u_randbytes(test_size), "test_data2.bin")
    u_bytes = load_bytes("test_data2.bin")
    user_input = raw_input(prompt).strip()
    if user_input == "q":
        exit()
    elif user_input == "s":
        pass
    else:
        examine_bytes(u_bytes)

    print "\n## Test 4: How good are our randint and u_randint functions()? ##\n"
    print "Generating %s randomn ints..." % test_size
    rand_ints = [blockrandom.randints(-200, 200) for i in range(test_size)]
    user_input = raw_input(prompt).strip()
    if user_input == "q":
        exit()
    elif user_input == "s":
        pass
    else:
        examine_bytes(rand_ints)

    print "Generating %s psuedorandomn ints..." % test_size
    u_rand_ints = [blockrandom.u_randints(-200, 200) for i in range(test_size)]
    user_input = raw_input(prompt).strip()
    if user_input == "q":
        exit()
    elif user_input == "s":
        pass
    else:
        examine_bytes(u_rand_ints)

    exit()

if __name__ == "__main__":
    interactive_tests()
