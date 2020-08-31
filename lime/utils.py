import ctypes
import mmap
from io import SEEK_SET, IOBase
from pathlib import Path

bitness = (ctypes.sizeof(ctypes.c_void_p)) * 8
maxAddressableSize = 1 << (bitness - 1) - 1  # signed size_t is used in python mmap!
maxAlignedAddressableSize = 1 << (bitness - 2)  # signed size_t is used in python mmap!
pageSize = mmap.PAGESIZE


def align(n: int) -> int:
	return n & ~(n & (pageSize - 1))


def transformForMappable(records):
	pageOffset = 0
	for dataStart, data in records:
		l = len(data)
		chunkStart = dataStart

		offsettedStart = chunkStart - pageOffset
		offsettedEnd = offsettedStart + l
		if offsettedEnd > maxAddressableSize:
			pageOffset = align(chunkStart)
			offsettedStart = chunkStart - pageOffset

		while l > maxAddressableSize:
			pageOffset = align(chunkStart)
			offsettedStart = chunkStart - pageOffset
			chunkEnd = pageOffset + maxAlignedAddressableSize
			chunkL = chunkEnd - chunkStart
			yield pageOffset, offsettedStart, data[chunkStart - dataStart : chunkEnd - dataStart]
			l -= chunkL
			chunkStart = chunkEnd

		offsettedStart = chunkStart - pageOffset
		chunkEnd = chunkStart + l
		yield pageOffset, offsettedStart, data[chunkStart - dataStart : chunkEnd - dataStart]


l = ctypes.CDLL(None)
fallocate_native = l.fallocate
fallocate_native.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_size_t, ctypes.c_size_t)
fallocate_native.restype = ctypes.c_int


def fallocate_path(file: Path, mode, offset, len):
	with file.open("r+") as f:
		return fallocate_file(f.fileno(), mode, offset, len)


def fallocate_file():
	return fallocate_native(f.fileno(), mode, offset, len)


def fallocate(file, mode, offset, len):
	if isinstance(file, Path):
		return fallocate_path(file, mode, offset, len)
	elif isinstance(file, IOBase):
		return fallocate_file(file, mode, offset, len)
	elif isinstance(file, int):
		return fallocate_native(file, mode, offset, len)


def dumpSparse(loaded, outFile: Path):
	#print(loaded)
	l = loaded[-1][0] + len(loaded[-1][1])
	#print("l", hex(l))

	with outFile.open("wb+") as of:
		fn = of.fileno()
		mode = 0
		fallocate_native(fn, mode, 0, l)
		prevOffset = None
		fM = None

		try:
			for offset, relStart, data in transformForMappable(loaded):
				if prevOffset != offset:
					if fM is not None:
						fM.__exit__(None, None, None)
					if offset < maxAddressableSize:
						#print("mapping", hex(min(l - offset, maxAlignedAddressableSize)), offset)
						fM = mmap.mmap(fn, min(l - offset, maxAlignedAddressableSize), flags=mmap.MAP_SHARED, access=mmap.ACCESS_WRITE, offset=offset).__enter__()
						prevOffset = offset
					else:
						fM = None
				if fM is not None:
					#print("relStart ", relStart, "len(data)", len(data))
					fM[relStart : (relStart + len(data))] = data
				else:
					#print("offset + relStart ", hex(offset + relStart))
					of.seek(offset + relStart, SEEK_SET)
					of.write(data)
					of.flush()
		finally:
			if fM is not None:
				fM.__exit__(None, None, None)
