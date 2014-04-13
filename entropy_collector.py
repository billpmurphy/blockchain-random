import multiprocessing, Queue, urllib2
from time import sleep
from operator import add
from json import loads

class HashCollectorDaemon(multiprocessing.Process):
    def __init__(self, url, queue, spare_queue, sysrandom):
        super(HashCollectorDaemon, self).__init__()
        self.most_recent = 0
        self._url = url
        self._queue = queue
        self._spare_queue = spare_queue
        self._sysrandom = sysrandom
    def run(self):
        self.stream_entropy()
    def get_unconfirmed_transactions(self):
        """
        Fetches the list of unconfirmed transactions from blockchain.info.
        """
        response = urllib2.urlopen(self._url)
        if response.code == 200:
            return loads(response.read())['txs']
        else:
            raise HTTPError("Status code: %s" % response.status_code)
    def fill_queue(self, transactions):
        """
        Fill the main queue and spare queue with entropy from recent transactions.
        """
        most_recent_trans = max((t['time'] for t in transactions))
        if most_recent_trans > self.most_recent:
            self.most_recent = most_recent_trans
            transactions = filter(lambda x: x > most_recent_trans, transactions)
            hex_hashes = reduce(add, (t['hash'] for t in transactions))
            bytes = bytearray.fromhex(hex_hashes)

            for byte in bytes[::-1]:
                try:
                    self._queue.put_nowait(byte)
                except Queue.Full:
                    pass
                try:
                    self._spare_queue.put_nowait(byte)
                except Queue.Full:
                    pass
    def stream_entropy(self):
        """
        Stream new entropy from blockchain.info.
        """
        transactions = []
        tries = 8
        while True:
            try:
                transactions = self.get_unconfirmed_transactions()
                tries = 8
            except (urllib2.HTTPError, urllib2.URLError):
                tries -= 1
                if tries <= 0:
                    stderr.write("WARNING: Cannot connect to blockchain.info")
            except Exception as e:
                self.terminate()
                raise e
            if len(transactions) > 0:
                self.fill_queue(transactions)
            sleep(10)
    def _use_cpu_entropy(self):
        """
        If, by some freak accident, we have nothing left in the spare cache,
        lean on Python's random.SystemRandom to get some entropy.
        """
        try:
            for byte in (self._sysrandom.randint(0, 256) for i in range(8)):
                self._spare_queue.put_nowait(byte)
        except Queue.Full:
            pass

