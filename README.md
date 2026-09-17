# NotebookLlama

Turn a PDF into a short podcast, the way NotebookLM does, with open models.

![image](https://github.com/user-attachments/assets/37296d45-f862-4a29-960f-4a1447a0da08)

Audio example: https://peregrine-results.s3.amazonaws.com/pigeon/Rg3RFytruIL15cOV3x_0.mp3

## How it works

One script, four steps, no GPU. The language models run on [Groq](https://groq.com), the voice runs on [PlayHT](https://play.ht).

| Step | What happens | Model |
|---|---|---|
| 1 | Clean the raw PDF text (page numbers, broken words, encoding junk) | Llama 3.1 8B |
| 2 | Write a conversational podcast script | Llama 3.3 70B |
| 3 | Make the script more dramatic without changing the message | Llama 3.1 8B |
| 4 | Speak it, with a preset voice or your own cloned voice | PlayHT |

## Run it

```bash
git clone https://github.com/ahkamboh/NotebookLlama
cd NotebookLlama
pip install -r requirements.txt

export GROQ_API_KEY=...        # console.groq.com
export PLAYHT_USER_ID=...      # play.ht -> API access
export PLAYHT_API_KEY=...

python app.py paper.pdf --out podcast.mp3
```

By default only the first 50 words are spoken, so a test run costs almost nothing on PlayHT. Add `--full` to voice the whole script, and `--voice <manifest url>` to use a cloned voice from your PlayHT account.

The script prints the final podcast text as well, so you can read it or feed it to another TTS.

## Use it from Python

```python
import asyncio
from app import NotebookLlama, ProcessingConfig

config = ProcessingConfig(preview_words=None, temperature=0.8)
result = asyncio.run(NotebookLlama(config).process_document("paper.pdf", "podcast.mp3"))
print(result["podcast_script"])
```

`ProcessingConfig` also lets you swap the three Groq models, change the chunk size for long PDFs, and set the PlayHT voice.

## Credits

The four-step idea comes from Meta's NotebookLlama tutorial in [llama-recipes](https://github.com/meta-llama/llama-recipes), which runs the models locally on a GPU. This repo is a single-file version of the same pipeline on hosted APIs, plus PlayHT voice cloning.

## License

MIT. See [LICENSE](LICENSE).
