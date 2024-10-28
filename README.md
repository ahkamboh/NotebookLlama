

# NotebookLlama: An Open Source version of NotebookLM

![image](https://github.com/user-attachments/assets/37296d45-f862-4a29-960f-4a1447a0da08)

## Audio Example
https://peregrine-results.s3.amazonaws.com/pigeon/Rg3RFytruIL15cOV3x_0.mp3

This is a guided series of tutorials/notebooks that can be taken as a reference or course to build a PDF to Podcast workflow with voice cloning capabilities. 

You will learn from experiments using Text to Speech Models and voice cloning technology.

It assumes zero knowledge of LLMs, prompting, audio models, and voice cloning - everything is covered in their respective notebooks.

### Outline:

Here is step by step thought (pun intended) for the task:

- Step 1: Pre-process PDF: Use `Llama-3.2-1B-Instruct` to pre-process the PDF and save it in a `.txt` file.
- Step 2: Transcript Writer: Use `Llama-3.1-70B-Instruct` model to write a podcast transcript from the text
- Step 3: Dramatic Re-Writer: Use `Llama-3.1-8B-Instruct` model to make the transcript more dramatic
- Step 4: Text-To-Speech Workflow: Use `parler-tts/parler-tts-mini-v1`, `bark/suno`, or `PlayHT` to generate a conversational podcast with optional voice cloning

Note 1: In Step 1, we prompt the 1B model to not modify the text or summarize it, strictly clean up extra characters or garbage characters that might get picked due to encoding from PDF. Please see the prompt in Notebook 1 for more details.

Note 2: For Step 2, you can also use `Llama-3.1-8B-Instruct` model, we recommend experimenting and trying if you see any differences. The 70B model was used here because it gave slightly more creative podcast transcripts for the tested examples.

Note 3: For Step 4, please try to extend the approach with other models. These models were chosen based on a sample prompt and worked best, newer models might sound better. Please see [Notes](./TTS_Notes.md) for some of the sample tests.

Note 4: For voice cloning capabilities, we've integrated PlayHT which allows you to either use preset voices or clone your own voice for more personalized audio generation. The voice cloning feature requires a PlayHT account and API credentials.

### Detailed steps on running the notebook:

Requirements: 
- GPU server or an API provider for using 70B, 8B and 1B Llama models
- For running the 70B model, you will need a GPU with aggregated memory around 140GB to infer in bfloat-16 precision
- PlayHT account and API credentials (for voice cloning)
- Audio sample for voice cloning (optional)

Note: For our GPU Poor friends, you can also use the 8B and lower models for the entire pipeline. There is no strong recommendation. The pipeline below is what worked best on first few tests. You should try and see what works best for you!

Before getting started:
1. Login using the `huggingface cli` and launch your jupyter notebook server
2. Get your Hugging Face access token from [here](https://huggingface.co/settings/tokens)
3. Run `huggingface-cli login` and paste your access token
4. Set up your PlayHT credentials if using voice cloning

Installation:
```bash
git clone https://github.com/meta-llama/llama-recipes
cd llama-recipes/recipes/quickstart/NotebookLlama/
pip install -r requirements.txt
```

### Notebook Walkthrough:

#### Notebook 1:
This notebook processes the PDF using the new Feather light model into a `.txt` file.
- Update the first cell with your PDF link
- Experiment with `Llama-3.2-1B-Instruct` model prompts

#### Notebook 2:
Takes processed output and creates a podcast transcript using `Llama-3.1-70B-Instruct`.
- Try the 405B model if GPU-rich
- Experiment with System prompts
- Compare with 8B model results

#### Notebook 3:
Adds dramatization using `Llama-3.1-8B-Instruct`.
- Creates conversation tuples for easier processing
- Customizes speaker-specific prompts
- Test with 3B and 1B models

#### Notebook 4:
Converts to podcast audio using multiple options:
1. Traditional approach:
   - `parler-tts/parler-tts-mini-v1`
   - `bark/suno` models
2. Voice Cloning approach (PlayHT):
   - Upload voice sample (30s - 1min recommended)
   - Use generated voice ID or preset voices
   - Generate high-quality TTS with cloned voice

Note: Parler requires transformers 4.43.3 or earlier, while steps 1-3 need the latest version.

### Next-Improvements/Further ideas:

- Speech Model experimentation with advanced voice cloning
- LLM vs LLM Debate feature
- Testing 405B for transcripts
- Better prompting strategies
- Support for website, audio, YouTube inputs
- Enhanced voice cloning capabilities
- Multi-speaker voice cloning support

### Resources for further learning:

- https://betterprogramming.pub/text-to-audio-generation-with-bark-clearly-explained-4ee300a3713a
- https://colab.research.google.com/drive/1dWWkZzvu7L9Bunq9zvD-W02RFUXoW-Pd?usp=sharing
- https://colab.research.google.com/drive/1eJfA2XUa-mXwdMy7DoYKVYHI1iTd9Vkt?usp=sharing#scrollTo=NyYQ--3YksJY
- https://replicate.com/suno-ai/bark?prediction=zh8j6yddxxrge0cjp9asgzd534
- https://suno-ai.notion.site/8b8e8749ed514b0cbf3f699013548683?v=bc67cff786b04b50b3ceb756fd05f68c
- https://docs.play.ht/reference/api-getting-started
- https://play.ht/voice-cloning

This project welcomes community contributions and PRs for any improvements!
