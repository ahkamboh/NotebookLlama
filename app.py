"""NotebookLlama: turn a PDF into a short podcast.

Pipeline (all hosted, no GPU needed):
  1. clean the PDF text        -> Llama 3.1 8B on Groq
  2. write a podcast script    -> Llama 3.3 70B on Groq
  3. make it more dramatic     -> Llama 3.1 8B on Groq
  4. speak it                  -> PlayHT text-to-speech (voice cloning optional)

Set GROQ_API_KEY, PLAYHT_USER_ID and PLAYHT_API_KEY in your environment, then:
  python app.py paper.pdf --out podcast.mp3
"""

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pypdf
from groq import Groq
from pyht import Client
from pyht.client import TTSOptions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_VOICE = (
    "s3://voice-cloning-zero-shot/a778f067-54d5-4e01-bc3a-3e7406dc0d2f/original/manifest.json"
)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is not set. Export it and run again.")
    return value


@dataclass
class ProcessingConfig:
    """Knobs for the pipeline."""

    temperature: float = 0.7
    max_tokens: int = 1500
    pdf_chunk_size: int = 4000
    # PlayHT bills per character. None = speak the whole script; a number = first N words only.
    preview_words: Optional[int] = 50
    voice: str = DEFAULT_VOICE
    clean_model: str = "llama-3.1-8b-instant"
    script_model: str = "llama-3.3-70b-versatile"
    drama_model: str = "llama-3.1-8b-instant"


class NotebookLlama:
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.groq = Groq(api_key=_require_env("GROQ_API_KEY"))
        self.playht = Client(
            user_id=_require_env("PLAYHT_USER_ID"),
            api_key=_require_env("PLAYHT_API_KEY"),
        )

    # ---- helpers -------------------------------------------------------------------------

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        reader = pypdf.PdfReader(pdf_path)
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)

    def _chunk_text(self, text: str, chunk_size: int) -> list:
        chunks, current, length = [], [], 0
        for word in text.split():
            if length + len(word) + 1 > chunk_size and current:
                chunks.append(" ".join(current))
                current, length = [word], len(word)
            else:
                current.append(word)
                length += len(word) + 1
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _chat(self, model: str, system: str, user: str) -> str:
        response = self.groq.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""

    # ---- pipeline ------------------------------------------------------------------------

    async def preprocess_pdf(self, pdf_path: str) -> str:
        """Step 1: clean up the raw PDF text chunk by chunk."""
        raw = self._extract_text_from_pdf(pdf_path)
        chunks = self._chunk_text(raw, self.config.pdf_chunk_size)
        logger.info("cleaning %d chunk(s) of PDF text", len(chunks))
        cleaned = [
            self._chat(
                self.config.clean_model,
                "Clean and structure this text. Keep its original meaning. Remove page "
                "numbers, broken hyphenation and encoding garbage. Do not summarize.",
                chunk,
            )
            for chunk in chunks
        ]
        return "\n".join(cleaned)

    async def generate_podcast_script(self, clean_text: str) -> str:
        """Step 2: turn the cleaned text into a conversational podcast script."""
        logger.info("writing podcast script")
        return self._chat(
            self.config.script_model,
            "Write an engaging podcast script from the following text. Make it "
            "conversational and easy to follow.",
            clean_text,
        )

    async def dramatize_script(self, podcast_script: str) -> str:
        """Step 3: add drama without changing the message."""
        logger.info("dramatizing script")
        return self._chat(
            self.config.drama_model,
            "Make this podcast script more dramatic and engaging while keeping its core message.",
            podcast_script,
        )

    async def generate_audio(self, script: str, output_path: str) -> str:
        """Step 4: text-to-speech with PlayHT."""
        words = script.split()
        if self.config.preview_words:
            words = words[: self.config.preview_words]
        text = " ".join(words)
        logger.info("generating audio for %d words", len(words))

        options = TTSOptions(voice=self.config.voice, format="mp3")
        audio = b"".join(chunk for chunk in self.playht.tts(text, options) if chunk)
        if not audio:
            raise RuntimeError("PlayHT returned no audio")
        with open(output_path, "wb") as f:
            f.write(audio)
        return output_path

    async def process_document(self, pdf_path: str, output_path: str = "podcast.mp3") -> Dict[str, Any]:
        try:
            clean_text = await self.preprocess_pdf(pdf_path)
            podcast_script = await self.generate_podcast_script(clean_text)
            dramatic_script = await self.dramatize_script(podcast_script)
            audio_path = await self.generate_audio(dramatic_script, output_path)
            return {
                "status": "success",
                "clean_text": clean_text,
                "podcast_script": podcast_script,
                "dramatic_script": dramatic_script,
                "audio_path": audio_path,
            }
        except Exception as e:  # keep the partial results useful to the caller
            logger.exception("pipeline failed")
            return {"status": "error", "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF -> podcast with Groq + PlayHT")
    parser.add_argument("pdf", help="path to the PDF")
    parser.add_argument("--out", default="podcast.mp3", help="output mp3 path")
    parser.add_argument(
        "--full", action="store_true", help="speak the whole script instead of a 50-word preview"
    )
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="PlayHT voice manifest URL")
    args = parser.parse_args()

    config = ProcessingConfig(preview_words=None if args.full else 50, voice=args.voice)
    result = asyncio.run(NotebookLlama(config).process_document(args.pdf, args.out))

    if result["status"] == "success":
        print(f"done: {result['audio_path']}")
        print("\n--- script ---\n")
        print(result["dramatic_script"])
    else:
        raise SystemExit(f"error: {result['error']}")


if __name__ == "__main__":
    main()
