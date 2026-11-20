"""The memory-mapped token table gives the same text vectors bit for bit.

Run: python -m unittest tests.test_model_memory
The SigLIP test needs open_clip and the cached ViT-B-16-SigLIP2 weights; it
is skipped without them (DOCUMENTARY_SIGLIP_TEST=0 skips it too).
"""
import importlib.util
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path.home() / ".gemini" / "scripts"))
if "documentary_materials" not in sys.modules:
    spec = importlib.util.spec_from_file_location("documentary_materials", ROOT / "__init__.py",
                                                  submodule_search_locations=[str(ROOT)])
    sys.modules["documentary_materials"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules["documentary_materials"])
from documentary_materials import model_memory  # noqa: E402

import torch  # noqa: E402


class _Text(torch.nn.Module):
    def __init__(self, vocab, width, dtype):
        super().__init__()
        self.token_embedding = torch.nn.Embedding(vocab, width).to(dtype)
        self.proj = torch.nn.Linear(width, 8).to(dtype)

    def forward(self, ids):
        return self.proj(self.token_embedding(ids)).mean(1)


class _Model(torch.nn.Module):
    def __init__(self, dtype=torch.float32):
        super().__init__()
        self.text = _Text(5000, 32, dtype)


class MappedTable(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = model_memory.CACHE
        model_memory.CACHE = Path(self.tmp.name)

    def tearDown(self):
        model_memory.CACHE = self.old
        import gc
        gc.collect()
        try:
            self.tmp.cleanup()
        except PermissionError:  # a memory map may still hold the file on Windows
            pass

    def _check(self, dtype):
        torch.manual_seed(0)
        model = _Model(dtype).eval()
        ids = torch.randint(0, 5000, (6, 64))
        with torch.no_grad():
            before = model.text(ids)
        self.assertTrue(model_memory.slim_text_table(model))
        self.assertNotIsInstance(model.text.token_embedding, torch.nn.Embedding)
        self.assertNotIn("text.token_embedding.weight", dict(model.named_parameters()))
        with torch.no_grad():
            after = model.text(ids)
        self.assertTrue(torch.equal(before, after))
        self.assertEqual(len(list(Path(self.tmp.name).glob("token_table_5000x32_*.bin"))), 1)

    def test_float32_rows_are_the_same(self):
        self._check(torch.float32)

    def test_float16_rows_are_the_same(self):
        self._check(torch.float16)

    def test_reuses_the_written_table(self):
        torch.manual_seed(1)
        a, b = _Model(), _Model()
        b.load_state_dict(a.state_dict())
        self.assertTrue(model_memory.slim_text_table(a))
        self.assertTrue(model_memory.slim_text_table(b))
        self.assertEqual(len(list(Path(self.tmp.name).glob("*.bin"))), 1)

    def test_other_models_are_left_alone(self):
        model = torch.nn.Module()
        self.assertFalse(model_memory.slim_text_table(model))
        scaled = _Model()
        scaled.text.token_embedding = torch.nn.Embedding(10, 4, max_norm=1.0)
        self.assertFalse(model_memory.slim_text_table(scaled))


@unittest.skipIf(os.environ.get("DOCUMENTARY_SIGLIP_TEST") == "0", "disabled")
class SigLIPText(unittest.TestCase):
    """The real model: every text vector picture_fit makes is unchanged."""

    def test_siglip2_text_vectors_unchanged(self):
        try:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            import open_clip
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
            from documentary_materials import picture_fit as pf
            tok = Tokenizer.from_file(hf_hub_download(pf.TOKENIZER, "tokenizer.json", local_files_only=True))
            model, _, _ = open_clip.create_model_and_transforms(pf.MODEL, pretrained=pf.PRETRAINED)
        except Exception as exc:  # no model on this machine
            self.skipTest(str(exc)[:200])
        tok.enable_truncation(64)
        tok.enable_padding(length=64, pad_id=tok.token_to_id("<pad>"))
        model.eval()
        texts = ["a herd of zebras crossing a brown river", "a crocodile lunges out of the water"] + list(pf.NEGATIVE)
        ids = torch.tensor([e.ids for e in tok.encode_batch(texts)])
        # The table file (786 MB) stays mapped while the model lives, so the
        # folder is removed only after the model is gone; left behind, every
        # test run kept 0.79 GB in %TEMP% (eleven of them on 2026-10-27).
        tmp = tempfile.mkdtemp()
        old, model_memory.CACHE = model_memory.CACHE, Path(tmp)
        try:
            with torch.no_grad():
                before = model.encode_text(ids)
                self.assertTrue(model_memory.slim_text_table(model))
                after = model.encode_text(ids)
            self.assertTrue(torch.equal(before, after))
        finally:
            model_memory.CACHE = old
            del model
            import gc
            gc.collect()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
