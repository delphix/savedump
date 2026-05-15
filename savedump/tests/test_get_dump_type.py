#
# Copyright 2026 Delphix
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#

import unittest
from unittest.mock import patch

from savedump.savedump import DumpType, get_dump_type


class GetDumpTypeTest(unittest.TestCase):
    """
    `get_dump_type()` shells out to `file(1)` and substring-matches the
    output against the values of the `DumpType` enum. These tests pin the
    expected behavior for each form of `file(1)` output we have seen in
    the field.
    """

    @staticmethod
    def _mock_file_output(output: str):
        return patch('savedump.savedump.shell_cmd', return_value=(True, output))

    def test_legacy_kdump_recognized(self) -> None:
        """
        Pre-2025.5.0.0 engines produced non-flattened kdumps; `file(1)`
        labels these with a capital-K "Kdump compressed dump".
        """
        output = ('foo.dump: Kdump compressed dump v6, '
                  'system Linux, node host, release 5.15.0, ...')
        with self._mock_file_output(output):
            self.assertEqual(get_dump_type('foo.dump'), DumpType.CRASHDUMP)

    def test_flattened_kdump_recognized(self) -> None:
        """
        2025.5.0.0+ engines produce flattened kdumps (kdump-tools
        unconditionally adds `-F` to makedumpfile). `file(1)` labels
        these with a lowercase-k "Flattened kdump compressed dump",
        which the original case-sensitive substring match against
        "Kdump compressed dump" missed -- see DLPX-95936.
        """
        output = ('foo.dump: Flattened kdump compressed dump v6, '
                  'system Linux, node host, release 6.17.0, ...')
        with self._mock_file_output(output):
            self.assertEqual(get_dump_type('foo.dump'), DumpType.CRASHDUMP)

    def test_userland_core_recognized(self) -> None:
        output = ('core: ELF 64-bit LSB core file, x86-64, version 1 '
                  '(SYSV), SVR4-style, from ...')
        with self._mock_file_output(output):
            self.assertEqual(get_dump_type('core'), DumpType.UCOREDUMP)

    def test_unknown_returns_none(self) -> None:
        output = 'foo.txt: ASCII text'
        with self._mock_file_output(output):
            self.assertIsNone(get_dump_type('foo.txt'))


if __name__ == '__main__':
    unittest.main()
