"""Check release split and input constraints without access to private audio."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code/a2_part_d_deployment"))
from revised_data import CLASSES, check_wav, examples, release_rows


class RevisedReleaseDataTest(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[1] / "final_annotation/consensus_gold_182.json").exists(),
                         "Private dataset not restored; run DVC pull and code/private_data.py restore")
    def test_partitions_are_disjoint_and_cover_the_corpus(self):
        groups = release_rows()
        self.assertEqual({name: len(rows) for name, rows in groups.items()},
                         {"train": 104, "validation": 38, "test": 40})
        speakers = [{row["original_speaker_id"] for row in rows} for rows in groups.values()]
        self.assertEqual(sum(map(len, speakers)), len(set.union(*speakers)))
        self.assertFalse({"P15", "P17", "P18", "P19"} & (speakers[0] | speakers[1]))
        self.assertEqual({row["intent"] for row in examples(groups)}, CLASSES)

    def test_audio_validation_rejects_the_wrong_sample_rate(self):
        with TemporaryDirectory() as directory:
            wav = Path(directory) / "sample.wav"
            for rate in (16000, 8000):
                with wave.open(str(wav), "wb") as stream:
                    stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                    stream.writeframes(bytes(rate * 2))
                if rate == 16000:
                    self.assertEqual(check_wav(wav), 1.0)
                else:
                    with self.assertRaisesRegex(ValueError, "16 kHz"):
                        check_wav(wav)


if __name__ == "__main__":
    unittest.main()
