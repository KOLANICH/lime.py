import struct
import sys
import typing
from collections.abc import ByteString, Mapping
from enum import IntEnum
from io import BytesIO
from warnings import warn

from rangeslicetools.tree import IndexProto, RangesTree
from rangeslicetools.utils import slen

__all__ = ("Signatures", "defaultFormat", "dumpRecord", "dump", "dumps", "load", "loads")


ByteStringT = typing.Union[ByteString, "mmap.mmap"]
_memFragTypeMap = (int, ByteStringT)
MemFragT = typing.Tuple[_memFragTypeMap]
MemFragIter = typing.Iterator[MemFragT]
MemFragMapping = typing.Mapping[_memFragTypeMap]


headerFormatStr = "IIQQQ"
headerSize = struct.calcsize(headerFormatStr)

headerStruct = {
	None: struct.Struct("=" + headerFormatStr),
	True: struct.Struct(">" + headerFormatStr),
	False: struct.Struct("<" + headerFormatStr),
}


class Signatures(IntEnum):
	LiME = struct.unpack(">I", b"LiME")[0]
	AVML = struct.unpack("<I", b"AVML")[0]

	@classmethod
	def _missing_(cls, value):
		raise ValueError("Invalid signature: " + repr(struct.pack("=I", value)), value)


compressionHeaderSizes = {
	Signatures.LiME: 0,
	Signatures.AVML: None  # ToDo!
}

# If the first byte is L, then the format is BE
formats = {
	Signatures.LiME: (0, lambda d: d, lambda d: d),
}
defaultFormat = Signatures.LiME

try:
	import snappy

	defaultFormat = Signatures.AVML
	formats[Signatures.AVML] = (1, snappy.decompress, snappy.compress)
except BaseException:
	warn("AVML format requires `snappy` compression. Install its lib and its python bindings.")


def dumpRecord(stream, start: int, data: ByteStringT, format: Signatures = defaultFormat, isBE: typing.Optional[bool] = None) -> int:
	version, processor, unprocessor = formats[format]
	stream.write(headerStruct[isBE].pack(format, version, start, start + len(data) - 1, 0))
	written = headerSize
	dataTransformed = unprocessor(data)
	stream.write(dataTransformed)
	written += len(dataTransformed)
	return written


def dump(t: MemFragMapping, stream, format: Signatures = defaultFormat, isBE: typing.Optional[bool] = None) -> int:
	if isinstance(t, Mapping):
		t = t.items()

	total = 0
	for k, v in t:
		total += dumpRecord(stream, k, v, format=format, isBE=isBE)
	return total


def dumps(t: MemFragMapping, format: Signatures = defaultFormat, isBE: typing.Optional[bool] = None) -> bytes:
	with BytesIO() as s:
		dump(t, s, format=format, isBE=isBE)
		#return s.getbuffer()
		return s.getvalue()


def sortOfsDataPairsList(ofsDataPairs) -> typing.List[MemFragT]:
	return sorted(ofsDataPairs, key=lambda x: x[0])


ctorCustomizers = {
	"rangeslicetools.tree": (
		"RangesTree", lambda loaded: RangesTree.build(*zip((slice(ofs, ofs + len(d)), d) for ofs, d in loaded))
	)
}


def estimateEmptySize(recordCount: int, format: Signatures) -> int:
	"""Estimates size of a dump blob containing all empty records. In this case there is no data, so no compression headers."""
	return recordCount * headerSize


def estimateMinSize(recordCount: int, format: Signatures) -> int:
	"""Estimates lower bound of size of a dump blob containing all nonempty records, assumming that every record data in compressed form occupies 0 bytes."""
	recordOverhead = headerSize + compressionHeaderSizes[format]
	return recordCount * recordOverhead


def estimateMaxSize(recordCount: int, totalDataSize: int, format: Signatures) -> int:
	"""Estimates upper bound of size of a dump blob. When compression is used, the overall size may be less, than predicted. When compression is used the overall size may be more than uncompressed depending on the data."""
	return estimateMinSize(recordCount=recordCount, format=format) + totalDataSize


def loadRecordNative(stream, desiredResultCtor=sortOfsDataPairsList) -> typing.Optional[MemFragT]:
	header = stream.read(headerSize)
	if not header:
		return None

	isBE = header[0] == ord(b"L")
	(format, version, start, end, padding) = headerStruct[isBE].unpack(header)

	format = Signatures(format)
	expectedVersion, processor, unprocessor = formats[format]

	if version != expectedVersion:
		raise ValueError("Version for the format must be ", format, expectedVersion)

	end += 1
	l = end - start
	if l < 0:
		raise ValueError("end < start", end, start)
	data = processor(stream.read(l))
	return (start, data)


def loadNative(stream) -> typing.Iterator[MemFragT]:
	r = loadRecordNative(stream)

	while r:
		yield r
		r = loadRecordNative(stream)


def loadKaitai(stream) -> typing.Iterator[MemFragT]:
	from kaitaistruct import KaitaiStream

	from lime.kaitai.lime_avml_memory_dump import LimeAvmlMemoryDump

	ks = KaitaiStream(stream)
	p = LimeAvmlMemoryDump(ks)
	for r in p.records:
		yield (r.header.range.start, r.payload)


def load(stream, desiredResultCtor=sortOfsDataPairsList, loaderBackend=loadNative):
	customizer = desiredResultCtor
	customizerDtor = ctorCustomizers.get(desiredResultCtor.__module__, None)
	if customizerDtor is not None:
		className, ctor = customizerDtor
		cls2Check = getattr(sys.modules[desiredResultCtor.__module__], className, None)
		if cls2Check is not None and isinstance(cls2Check, type) and issubclass(desiredResultCtor, cls2Check):
			customizer = ctor

	return desiredResultCtor(loaderBackend(stream))


def loads(d, desiredResultCtor=sortOfsDataPairsList, loaderBackend=loadNative) -> MemFragMapping:
	with BytesIO(d) as s:
		return load(s, desiredResultCtor=desiredResultCtor, loaderBackend=loaderBackend)
