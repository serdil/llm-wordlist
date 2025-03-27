# LLM Wordlist Filter

A tool to score and filter a list of words from a text file using an LLM from OpenRouter. The tool first scores words based on a provided prompt, then allows filtering out words with scores below a specified threshold.

## Features

- Score words using Claude 3.5 Sonnet or other models from OpenRouter
- Use a custom prompt to score words

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/serdil/llm-wordlist.git
   cd llm-wordlist
   ```

2. Create a virtual environment and install dependencies using uv:
   ```
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. Create a `.env` file with your OpenRouter API key:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to add your OpenRouter API key.

## Usage

The tool provides two main commands:
1. `score` - Score words using an LLM and save the scores
2. `filter` - Filter already scored words based on a threshold

### Scoring Words

Basic usage:

```
python main.py score input_words.txt
```

This will:
1. Read words from `input_words.txt` (one word per line)
2. Read the prompt from `prompt.txt`
3. Score the words using Claude 3.5 Sonnet
4. Save all words with scores to `all_words_scores.txt`

Advanced options:

```
python main.py score input_words.txt --prompt-file custom_prompt.txt --all-scores-file all_scores.txt --model anthropic/claude-3-opus --batch-size 50 --debug
```

### Filtering Already Scored Words

If you already have a file with scored words (in the format "word:score"), you can filter them without re-scoring:

```
python main.py filter --min-score 85
```

This will:
1. Read scored words from `all_words_scores.txt`
2. Filter out words with scores below 85
3. Save the filtered words to `filtered_words.txt`

Advanced options:

```
python main.py filter --input-file custom_scores.txt --output-file custom_filtered.txt --min-score 95
```

### Command-line Arguments

#### Score Command

- `input_file`: Path to the input file containing words (one per line)
- `--prompt-file`: Path to the file containing the prompt (default: prompt.txt)
- `--all-scores-file`: Path to save all words with scores (default: all_words_scores.txt)
- `--model`: OpenRouter model to use (default: from .env or claude-3.5-sonnet)
- `--batch-size`: Number of words to process in each batch (default: 100)
- `--debug`: Enable debug output

#### Filter Command

- `--input-file`: Path to the input file containing scored words (default: all_words_scores.txt)
- `--output-file`: Path to save the filtered words (default: filtered_words.txt)
- `--min-score`: Minimum score to keep a word (default: 90)

## Prompt Format

The prompt should instruct the LLM to score words and return them in the format:

```
word:score
word:score
```

A sample prompt is provided in `prompt.txt`.

## Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `DEFAULT_MODEL`: Default model to use (e.g., anthropic/claude-3.5-sonnet)

## Examples

### Scoring Example

Input file (`words.txt`):
```
elma
özgürlük
mikroskop
kalem
```

After running the score command:
```
python main.py score words.txt
```

All scores file (`all_words_scores.txt`):
```
elma:95
özgürlük:80
mikroskop:75
kalem:90
```

Then, to filter words with a minimum score of 90:
```
python main.py filter --min-score 90
```

This produces a filtered words file (`filtered_words.txt`):
```
elma
kalem
```

### Filtering Example

If you already have the scored words file (`all_words_scores.txt`):
```
elma:95
özgürlük:80
mikroskop:75
kalem:90
```

You can filter it with different thresholds:

```
python main.py filter --min-score 80
```

Output file (`filtered_words.txt`):
```
elma
özgürlük
kalem
```

## License

MIT
