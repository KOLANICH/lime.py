# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from enum import Enum

import kaitaistruct
from kaitaistruct import BytesIO, KaitaiStream, KaitaiStruct
from pkg_resources import parse_version

if parse_version(kaitaistruct.__version__) < parse_version("0.9"):
	raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))


class LimeAvmlMemoryDump(KaitaiStruct):
	"""Just a file format for memory dumps. It may be better to use it instead of raw sparse files, when it is needed to transfer a dump.
	It is also damn simple, so third-party apps may also adopt it.

	LiME is a GPL-licensed Linux kernel module for acquiring memory dumps.
	AVLM is a MIT-licensed app by Microsoft, using its format and extending it.

	To acquire a dump of 2 records on Linux:
	  sudo apt-get install -y lime-forensics-dkms
	  sudo insmod /lib/modules/`uname -r`/updates/dkms/lime.ko "path=tcp:4444 format=lime dio=1 localhostonly=1"
	  #in an another tab
	  nc localhost 4444 | dd bs=1 count=647232 > ram.lime
	  ^C
	  #in the first tab
	  sudo rmmod lime

	.. seealso::
	   Source - https://github.com/microsoft/avml/blob/4409f0048854e44d9b4d0f2c31261acb43174e92/src/image.rs#L22


	.. seealso::
	   Source - https://github.com/504ensicsLabs/LiME/tree/master/doc#Spec
	"""

	def __init__(self, _io, _parent=None, _root=None):
		self._io = _io
		self._parent = _parent
		self._root = _root if _root else self
		self._read()

	def _read(self):
		self.records = []
		i = 0
		while not self._io.is_eof():
			self.records.append(LimeAvmlMemoryDump.Record(self._io, self, self._root))
			i += 1

	class Record(KaitaiStruct):
		def __init__(self, _io, _parent=None, _root=None):
			self._io = _io
			self._parent = _parent
			self._root = _root if _root else self
			self._read()

		def _read(self):
			self.header = LimeAvmlMemoryDump.Record.Header(self._io, self, self._root)
			self.payload = self._io.read_bytes(self.header.range.size)

		class Range(KaitaiStruct):
			def __init__(self, _io, _parent=None, _root=None):
				self._io = _io
				self._parent = _parent
				self._root = _root if _root else self
				self._read()

			def _read(self):
				self.start = self._io.read_u8le()
				self.end_closed = self._io.read_u8le()

			@property
			def end(self):
				if hasattr(self, "_m_end"):
					return self._m_end if hasattr(self, "_m_end") else None

				self._m_end = self.end_closed + 1
				return self._m_end if hasattr(self, "_m_end") else None

			@property
			def size(self):
				if hasattr(self, "_m_size"):
					return self._m_size if hasattr(self, "_m_size") else None

				self._m_size = self.end - self.start
				return self._m_size if hasattr(self, "_m_size") else None

		class FormatIdentifier(KaitaiStruct):
			class Format(Enum):
				unknown = 0
				lime = 1
				avml = 2

			def __init__(self, _io, _parent=None, _root=None):
				self._io = _io
				self._parent = _parent
				self._root = _root if _root else self
				self._read()

			def _read(self):
				self.signature0 = (self._io.read_bytes(1)).decode(u"ascii")
				self.signature1 = (self._io.read_bytes(3)).decode(u"ascii")

			@property
			def is_be(self):
				if hasattr(self, "_m_is_be"):
					return self._m_is_be if hasattr(self, "_m_is_be") else None

				self._m_is_be = self.signature0 == u"L"
				return self._m_is_be if hasattr(self, "_m_is_be") else None

			@property
			def is_avlm(self):
				if hasattr(self, "_m_is_avlm"):
					return self._m_is_avlm if hasattr(self, "_m_is_avlm") else None

				self._m_is_avlm = (((self.signature0 == u"A") and (self.signature1 == u"VML"))) or (((self.is_be) and (self.signature1 == u"MVA")))
				return self._m_is_avlm if hasattr(self, "_m_is_avlm") else None

			@property
			def format(self):
				if hasattr(self, "_m_format"):
					return self._m_format if hasattr(self, "_m_format") else None

				self._m_format = LimeAvmlMemoryDump.Record.FormatIdentifier.Format.lime if self.is_lime else (LimeAvmlMemoryDump.Record.FormatIdentifier.Format.avml if self.is_avlm else LimeAvmlMemoryDump.Record.FormatIdentifier.Format.unknown)
				return self._m_format if hasattr(self, "_m_format") else None

			@property
			def is_lime(self):
				if hasattr(self, "_m_is_lime"):
					return self._m_is_lime if hasattr(self, "_m_is_lime") else None

				self._m_is_lime = (((self.signature0 == u"E") and (self.signature1 == u"MiL"))) or (((self.is_be) and (self.signature1 == u"iME")))
				return self._m_is_lime if hasattr(self, "_m_is_lime") else None

			@property
			def is_valid(self):
				if hasattr(self, "_m_is_valid"):
					return self._m_is_valid if hasattr(self, "_m_is_valid") else None

				self._m_is_valid = self.format != LimeAvmlMemoryDump.Record.FormatIdentifier.Format.unknown
				return self._m_is_valid if hasattr(self, "_m_is_valid") else None

		class Header(KaitaiStruct):
			def __init__(self, _io, _parent=None, _root=None):
				self._io = _io
				self._parent = _parent
				self._root = _root if _root else self
				self._read()

			def _read(self):
				self.format_identifier = self._io.read_bytes(4)
				self.version = self._io.read_u4le()
				self.range = LimeAvmlMemoryDump.Record.Range(self._io, self, self._root)
				self.padding = self._io.read_bytes(8)

			@property
			def valid_version_must_be(self):
				if hasattr(self, "_m_valid_version_must_be"):
					return self._m_valid_version_must_be if hasattr(self, "_m_valid_version_must_be") else None

				self._m_valid_version_must_be = self._parent.format_identifier.format.value
				return self._m_valid_version_must_be if hasattr(self, "_m_valid_version_must_be") else None

			@property
			def is_valid(self):
				if hasattr(self, "_m_is_valid"):
					return self._m_is_valid if hasattr(self, "_m_is_valid") else None

				self._m_is_valid = (self._parent.format_identifier.is_valid) and (self.version == self.valid_version_must_be)
				return self._m_is_valid if hasattr(self, "_m_is_valid") else None

		@property
		def format_identifier(self):
			if hasattr(self, "_m_format_identifier"):
				return self._m_format_identifier if hasattr(self, "_m_format_identifier") else None

			_pos = self._io.pos()
			self._io.seek(0)
			self._m_format_identifier = LimeAvmlMemoryDump.Record.FormatIdentifier(self._io, self, self._root)
			self._io.seek(_pos)
			return self._m_format_identifier if hasattr(self, "_m_format_identifier") else None
