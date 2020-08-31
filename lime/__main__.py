import inspect
import sys
from os import isatty, truncate
from pathlib import Path

from plumbum import cli

from . import Signatures, defaultFormat, dump, load
from .testTools import estimateMaxRandDumpSize, genRandDump
from .utils import *


class LiMECLI(cli.Application):
	pass


@LiMECLI.subcommand("2sparse")
class LiME2Sparse(cli.Application):
	def main(self, limeFile):
		limeFile = Path(limeFile)
		outFile = limeFile.parent / limeFile.stem

		with limeFile.open("rb") as iF:
			lFn = iF.fileno()
			with mmap.mmap(lFn, limeFile.stat().st_size, access=mmap.ACCESS_READ) as lM:
				loaded = load(lM)
				dumpSparse(loaded, outFile)


class DumpCommand(cli.Application):
	format = cli.SwitchAttr(["-f", "--format"], Signatures, default=defaultFormat, help="Selects the format to be used")


def genParams(f, locs, randDumpArgs):
	for par in inspect.signature(f).parameters.values():
		shortArfName, doc = randDumpArgs[par.name]
		locs[par.name] = cli.SwitchAttr(["-" + shortArfName, "--" + par.name], par.annotation, help=doc, default=par.default)


@LiMECLI.subcommand("genRand")
class RandDump(DumpCommand):
	genParams(
		genRandDump,
		locals(),
		{
			"count": ("c", "sets count of records"),
			"minAddr": ("a", "sets minimum address of a dump"),
			"maxAddr": ("A", "sets maximum address of a dump"),
			"minSize": ("s", "Sets minimum size of uncompressed data in the record"),
			"maxSize": ("S", "Sets maximum size of uncompressed data in the record"),
		},
	)

	def dumpRandomData(self, buf):
		l = estimateMaxRandDumpSize(count=self.count, maxSize=self.maxSize, format=self.format)
		dI = list(genRandDump(count=self.count, minAddr=self.minAddr, minSize=self.minSize, maxSize=self.maxSize, maxAddr=self.maxAddr))  # iterator, evaluates lazily
		fn = buf.fileno()
		fallocate_native(fn, 0, 0, l)
		l = 0
		with mmap.mmap(fn, l, flags=mmap.MAP_SHARED, access=mmap.ACCESS_WRITE) as fM:
			l = dump(dI, fM, format=self.format)
		truncate(fn, l)

	def main(self, limeFile="-"):
		if limeFile == "-":
			buf = sys.stdout.buffer
			if isatty(buf.fileno()):
				raise Exception("Refusing output binary data into terminal!")
			self.dumpRandomData(buf)
		else:
			with open(limeFile, "wb+") as buf:
				self.dumpRandomData(buf)


if __name__ == "__main__":
	LiMECLI.run()
