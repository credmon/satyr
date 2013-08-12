#!/usr/bin/env python

import unittest
from test_helpers import *

contents = load_input_contents('../json_files/core-01')
threads_expected = 2
frames_expected = 6
expected_short_text = '''#1 raise in /usr/lib64/libc-2.15.so
#2 abort in /usr/lib64/libc-2.15.so
#3 92ebaf825e4f492952c45189cb9ffc6541f8599b+1123 in /usr/bin/will_abort
#4 __libc_start_main in /usr/lib64/libc-2.15.so
'''

class TestCoreStacktrace(BindingsTestCase):
    def setUp(self):
        self.trace = satyr.CoreStacktrace(contents)

    def test_correct_thread_count(self):
        self.assertEqual(len(self.trace.threads), threads_expected)

    def test_correct_frame_count(self):
        self.assertEqual(frame_count(self.trace), frames_expected)

    def test_dup(self):
        dup = self.trace.dup()
        self.assertNotEqual(id(dup.threads), id(self.trace.threads))
        self.assertEqual(dup.threads, self.trace.threads)

        dup.threads = dup.threads[:5]
        dup2 = dup.dup()
        self.assertEqual(len(dup.threads), len(dup2.threads))
        self.assertNotEqual(id(dup.threads), id(dup2.threads))

    def test_prepare_linked_list(self):
        dup = self.trace.dup()
        dup.threads = dup.threads[:5]
        dup2 = dup.dup()
        self.assertTrue(len(dup.threads) <= 5)

    def test_str(self):
        out = str(self.trace)
        self.assertTrue(('Core stacktrace with %d threads' % threads_expected) in out)

    def test_to_short_text(self):
        self.assertEqual(self.trace.to_short_text(8), expected_short_text)

    def test_bthash(self):
        self.assertEqual(self.trace.get_bthash(), '6ebee2edb486ee24a3280c18b0db5353bbc22014')

    def test_getset(self):
        self.assertGetSetCorrect(self.trace, 'signal', 6, 42)
        self.assertGetSetCorrect(self.trace, 'executable', '/usr/bin/will_abort', '/bin/true')

    def test_crash_thread(self):
        self.assertTrue(self.trace.crash_thread is self.trace.threads[1])

class TestCoreThread(BindingsTestCase):
    def setUp(self):
        self.thread = satyr.CoreStacktrace(contents).threads[0]

    def test_cmp(self):
        self.assertEqual(self.thread, self.thread)
        dup = self.thread.dup()
        self.assertEqual(self.thread, dup)
        dup.frames[0].build_id = 'wut'
        self.assertNotEqual(self.thread, dup)

    def test_duphash(self):
        expected_plain = '''Thread
92ebaf825e4f492952c45189cb9ffc6541f8599b+0x2a
92ebaf825e4f492952c45189cb9ffc6541f8599b+0x29ee
'''
        self.assertEqual(self.thread.get_duphash(flags=satyr.DUPHASH_NOHASH, frames=3), expected_plain)
        self.assertEqual(self.thread.get_duphash(), 'ad8486fa45ff39ffed7a07f3b68b8f406ebe2550')

class TestCoreFrame(BindingsTestCase):
    def setUp(self):
        self.frame = satyr.CoreStacktrace(contents).threads[1].frames[0]

    def test_str(self):
        out = str(self.frame)
        self.assertEquals(out, '[0x0000003739a35935] raise cc10c72da62c93033e227ffbe2670f2c4fbbde1a+0x35935 '
                               '[/usr/lib64/libc-2.15.so] '
                               'fingerprint: f33186a4c862fb0751bca60701f553b829210477 (hashed)')

    def test_dup(self):
        dup = self.frame.dup()
        self.assertEqual(dup, self.frame)

        dup.function_name = 'other'
        self.assertNotEqual(dup, self.frame)

    def test_cmp(self):
        dup = self.frame.dup()
        self.assertEqual(dup, dup)
        self.assertEqual(dup, self.frame)
        self.assertEqual(dup, self.frame)
        self.assertNotEqual(id(dup), id(self.frame))
        dup.function_name = 'another'
        self.assertNotEqual(dup, self.frame)
        self.assertFalse(dup > self.frame)
        self.assertTrue(dup < self.frame)

    def test_getset(self):
        self.assertGetSetCorrect(self.frame, 'address', 237190207797, 5000)
        self.assertGetSetCorrect(self.frame, 'build_id', 'cc10c72da62c93033e227ffbe2670f2c4fbbde1a', 'abcdef')
        self.assertGetSetCorrect(self.frame, 'build_id_offset', 219445, 44)
        self.assertGetSetCorrect(self.frame, 'function_name', 'raise', 'lower')
        self.assertGetSetCorrect(self.frame, 'file_name', '/usr/lib64/libc-2.15.so', '/u/l/x')
        self.assertGetSetCorrect(self.frame, 'fingerprint', 'f33186a4c862fb0751bca60701f553b829210477', 'xxx')
        self.assertGetSetCorrect(self.frame, 'fingerprint_hashed', True, False)


if __name__ == '__main__':
    unittest.main()