#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""dataset.py - PyTorch Dataset Loader with Zero Administrative Features.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Guarantees:
1. Strips all speaker, file, recording, and timing metadata.
2. Yields strictly (transcript_text, intent_label_id).
3. Encodes target intent classes deterministically.
"""

from typing import List, Dict, Tuple
import torch
from torch.utils.data import Dataset

# Canonical 4-class intent target mapping
INTENT_CLASSES = ["admissions", "hostel_mess", "it_support", "student_services"]
INTENT2ID = {cls: idx for idx, cls in enumerate(INTENT_CLASSES)}
ID2INTENT = {idx: cls for idx, cls in enumerate(INTENT_CLASSES)}

class HelpdeskDataset(Dataset):
    def __init__(self, samples: List[Dict], tokenizer=None, max_length: int = 128):
        """
        samples: list of dicts with 'transcript' and 'gold_intent'.
        """
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        text = sample["transcript"]
        label_str = sample["gold_intent"]
        label_id = INTENT2ID.get(label_str, 0)

        if self.tokenizer:
            encoding = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt"
            )
            item = {key: val.squeeze(0) for key, val in encoding.items()}
            item["labels"] = torch.tensor(label_id, dtype=torch.long)
            return item
        else:
            return {
                "text": text,
                "label": torch.tensor(label_id, dtype=torch.long),
                "intent_name": label_str
            }

if __name__ == "__main__":
    dummy = [
        {"transcript": "Hostel room wifi is slow", "gold_intent": "it_support"},
        {"transcript": "What is the MTech cutoff?", "gold_intent": "admissions"}
    ]
    ds = HelpdeskDataset(dummy)
    print("Dataset length:", len(ds))
    print("Sample 0:", ds[0])
