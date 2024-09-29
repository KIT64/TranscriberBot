import os
import unittest
from tgbot.utils import split_audio, get_duration


class TestAudioUtils(unittest.TestCase):
    def setUp(self):
        self.test_audio_path = os.path.join(os.path.dirname(__file__), 'test_audio.m4a')

        if not os.path.exists(self.test_audio_path):
            raise FileNotFoundError(f"Test audio file not found: {self.test_audio_path}")

    def test_split_audio_with_real_file(self):
        total_duration = get_duration(self.test_audio_path)
        max_chunk_duration = 5 * 60  #  in seconds
        expected_chunks = -(-total_duration // max_chunk_duration)  # Ceiling division
        extension = os.path.splitext(self.test_audio_path)[1][1:]  # Get file extension without the dot

        chunks = split_audio(self.test_audio_path, max_chunk_duration, extension)
        
        self.assertEqual(
            len(chunks),
            expected_chunks,
            f"Expected {expected_chunks} chunks, but got {len(chunks)}",
        )

        for chunk_path in chunks:
            self.assertTrue(os.path.exists(chunk_path), f"Chunk file not found: {chunk_path}")

        for chunk_path in chunks:
            if chunk_path != self.test_audio_path:
                os.remove(chunk_path)

    def test_get_duration_accuracy(self):
        # Test the accuracy of get_duration function
        actual_duration = get_duration(self.test_audio_path)
        expected_duration = 89.5  # Assuming the test_audio.mp3 is 60 seconds long
        
        self.assertAlmostEqual(
            actual_duration,
            expected_duration,
            delta=0.5,  # Allow for a 0.5-second difference for more precision
            msg=f"Expected duration of {expected_duration} seconds, but got {actual_duration} seconds",
        )

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestAudioUtils('test_split_audio_with_real_file'))
    # suite.addTest(TestAudioUtils('test_get_duration_accuracy'))
    
    runner = unittest.TextTestRunner()
    runner.run(suite)
