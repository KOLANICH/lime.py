import typing
from random import _urandom, randint

from . import MemFragT, Signatures, estimateMaxSize
from .utils import maxAddressableSize


def genRandRecord(minAddr: int = 0, minSize: int = 10, maxSize: int = 20, maxAddr: int = maxAddressableSize) -> MemFragT:
	start = randint(minAddr, maxAddr - minSize)
	stop = randint(start + minSize, min(start + maxSize, maxAddr))
	len = stop - start
	payload = _urandom(len)
	return (start, payload)


def genRandDump(count: int = 10, minAddr: int = 0, minSize: int = 10, maxSize: int = 20, maxAddr: int = maxAddressableSize) -> typing.Iterator[MemFragT]:
	prevLen = None
	for i in range(count):
		rec = genRandRecord(minAddr=minAddr, minSize=minSize, maxSize=maxSize, maxAddr=maxAddr - maxSize * (count - i))
		yield rec
		prevLen = len(rec[1])
		minAddr = rec[0] + prevLen
		rec = None


def estimateMaxRandDumpSize(count: int, maxSize: int, format: Signatures) -> int:
	return estimateMaxSize(recordCount=count, totalDataSize=maxSize * count, format=format)
