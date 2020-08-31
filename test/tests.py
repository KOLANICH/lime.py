#!/usr/bin/env python3
import typing
import itertools
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

from lime import *
from lime import Signatures, headerStruct
from lime.testTools import *


class Tests(unittest.TestCase):
	def test_roundtrip(self):
		d = list(genRandDump())
		for isBE in headerStruct.keys():
			for format in Signatures:
				with self.subTest(format=format, isBE=isBE):
					f = dumps(d, format=format, isBE=isBE)
					d1 = loads(f)
					self.assertEqual(d, d1)
					f1 = dumps(d, format=format, isBE=isBE)


if __name__ == "__main__":
	unittest.main()
