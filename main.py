import argparse
import json
import locale
import os
import sys
from typing import List, Dict

import requests
from dotenv import load_dotenv


def main():
    """Main function to run the word filtering process."""
    # Parse command line arguments
    args = parse_arguments()

    if args.command == 'filter':
        # Filter already scored words
        filter_scored_words(args.input_file, args.output_file, args.min_score)
    else:  # args.command == 'score'
        # Load environment variables
        load_dotenv()

        # Get API key from environment
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("Error: OPENROUTER_API_KEY not found in environment variables.")
            print("Please create a .env file with your OpenRouter API key.")
            sys.exit(1)

        # Get model from arguments or environment or default
        model = args.model or os.getenv('DEFAULT_MODEL') or "anthropic/claude-3.5-sonnet"

        # Read words from input file
        print(f"Reading words from {args.input_file}...")
        words = read_words_from_file(args.input_file)
        print(f"Read {len(words)} words.")

        # Read prompt from file
        print(f"Reading prompt from {args.prompt_file}...")
        prompt = read_prompt_from_file(args.prompt_file)

        # Print the prompt for debugging
        debug_print(args.debug, "\nPrompt being used:")
        debug_print(args.debug, "-----------------")
        debug_print(args.debug, prompt)
        debug_print(args.debug, "-----------------\n")

        # Score words using the LLM in batches and persist results
        print(f"Scoring words using {model} in batches of {args.batch_size}...")
        all_scores = score_words_with_llm(
            words,
            prompt,
            model,
            api_key,
            batch_size=args.batch_size,
            all_scores_file=args.all_scores_file,
            debug=args.debug
        )

        # Print summary
        print(f"Processed {len(all_scores)} words. Use the 'filter' command to filter words based on scores.")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Filter words using an LLM from OpenRouter.')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Score command - original functionality
    score_parser = subparsers.add_parser('score', help='Score words using an LLM')
    score_parser.add_argument('input_file', help='Path to the input file containing words (one per line)')
    score_parser.add_argument('--prompt-file', default='prompt.txt', help='Path to the file containing the prompt (default: prompt.txt)')
    score_parser.add_argument('--all-scores-file', default='all_words_scores.txt', help='Path to save all words with scores (default: all_words_scores.txt)')
    score_parser.add_argument('--model', help='OpenRouter model to use (default: from .env or claude-3.5-sonnet)')
    score_parser.add_argument('--batch-size', type=int, default=100, help='Number of words to process in each batch (default: 100)')
    score_parser.add_argument('--debug', action='store_true', help='Enable debug output')

    # Filter command - new functionality
    filter_parser = subparsers.add_parser('filter', help='Filter already scored words based on a threshold')
    filter_parser.add_argument('--input-file', default='all_words_scores.txt', help='Path to the input file containing scored words (default: all_words_scores.txt)')
    filter_parser.add_argument('--output-file', default='filtered_words.txt', help='Path to save the filtered words (default: filtered_words.txt)')
    filter_parser.add_argument('--min-score', type=int, default=90, help='Minimum score to keep a word (default: 90)')

    # For backward compatibility, if no command is provided, default to 'score'
    args = parser.parse_args()
    if args.command is None:
        # If no command is provided but an input file is (old style), assume 'score'
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            args.command = 'score'
            args.input_file = sys.argv[1]
        else:
            parser.print_help()
            sys.exit(1)

    return args


def filter_scored_words(input_file: str, output_file: str, min_score: int):
    """
    Filter already scored words based on a threshold.

    Args:
        input_file: Path to the input file containing scored words (word:score format)
        output_file: Path to save the filtered words
        min_score: Minimum score to keep a word
    """
    try:
        # Read scored words from input file
        print(f"Reading scored words from {input_file}...")
        all_scores = {}
        total_lines = 0
        skipped_lines = 0
        duplicate_words = 0

        with open(input_file, 'r', encoding='utf-8') as file:
            for line in file:
                total_lines += 1
                line = line.strip()
                if not line:
                    skipped_lines += 1
                    continue
                if ':' not in line:
                    print(f"Warning: Line {total_lines} does not contain a colon: '{line}'")
                    skipped_lines += 1
                    continue

                word, score_str = line.split(':', 1)
                word = word.strip()

                try:
                    score = int(score_str.strip())
                    if word in all_scores:
                        duplicate_words += 1
                        # Keep the highest score for duplicate words
                        all_scores[word] = max(all_scores[word], score)
                    else:
                        all_scores[word] = score
                except ValueError:
                    print(f"Warning: Line {total_lines} does not have a valid integer score: '{line}'")
                    skipped_lines += 1
                    continue

        print(f"Total lines in file: {total_lines}")
        print(f"Skipped lines: {skipped_lines}")
        print(f"Duplicate words: {duplicate_words}")
        print(f"Read {len(all_scores)} unique scored words.")

        # Filter words based on threshold
        filtered_words = {word: score for word, score in all_scores.items() if score >= min_score}

        # Save filtered words to output file
        with open(output_file, 'w', encoding='utf-8') as file:
            # Sort words according to Turkish alphabet
            for word in sorted(filtered_words.keys(), key=turkish_sort_key):
                file.write(f"{word}\n")

        print(f"Filtered {len(filtered_words)} words with scores >= {min_score}.")
        print(f"Filtered words saved to {output_file}")

    except Exception as e:
        print(f"Error filtering words: {e}")
        sys.exit(1)


def read_words_from_file(file_path: str) -> List[str]:
    """Read words from a text file, one word per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def read_prompt_from_file(file_path: str) -> str:
    """Read the prompt from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Prompt file '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        sys.exit(1)


def score_words_with_llm(words: List[str], prompt: str, model: str, api_key: str,
                         batch_size: int = 100,
                         all_scores_file: str = "all_words_scores.txt",
                         debug: bool = False) -> Dict[str, int]:
    """
    Score words using the specified LLM model via OpenRouter API.
    Processes words in batches and persists results after each batch.
    Returns a dictionary of all word scores.
    """
    if not words:
        return {}

    # Initialize all_scores_file
    with open(all_scores_file, 'w', encoding='utf-8') as all_file:
        pass  # Create empty file

    all_scores = {}

    # Process words in batches
    for i in range(0, len(words), batch_size):
        batch = words[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(words) + batch_size - 1)//batch_size} ({len(batch)} words)...")

        # Score the current batch
        batch_scores = score_words_batch_with_llm(batch, prompt, model, api_key, debug=debug)

        # Update all scores dictionary
        all_scores.update(batch_scores)

        # Persist results immediately
        with open(all_scores_file, 'a', encoding='utf-8') as all_file:
            for word, score in batch_scores.items():
                all_file.write(f"{word}:{score}\n")

    return all_scores


def score_words_batch_with_llm(words_batch: List[str], prompt: str, model: str, api_key: str, debug: bool = False) -> Dict[str, int]:
    """
    Score a batch of words using the specified LLM model via OpenRouter API.
    Uses prompt caching for efficiency.
    """
    if not words_batch:
        return {}

    # Prepare the API request
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "LLM Wordlist Filter"
    }

    # Join words with newlines for the prompt
    words_text = "\n".join(words_batch)

    # Prepare the payload with prompt caching
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                        "cache_control": {"type": "ephemeral"}  # Cache the static prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": words_text
                    }
                ]
            }
        ]
    }

    # Log the request content for debugging
    debug_print(debug, "Request content:")
    debug_print(debug, json.dumps(payload, indent=2))
    debug_print(debug, "")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()

            # Log the full API response for debugging
            debug_print(debug, "Full API response:")
            debug_print(debug, json.dumps(result, indent=2))
            debug_print(debug, "")

            # Check if choices array exists and is not empty
            if "choices" in result and result["choices"] and "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                content = result["choices"][0]["message"]["content"]

                # Log the raw LLM response content to the console for debugging
                debug_print(debug, "Raw LLM response content:")
                debug_print(debug, content)
                debug_print(debug, "")

                # Parse the response to extract word:score pairs
                scores = {}
                for line in content.strip().split('\n'):
                    if ':' in line:
                        word, score_str = line.split(':', 1)
                        try:
                            score = int(score_str.strip())
                            scores[word.strip()] = score
                        except ValueError:
                            # Skip lines that don't have a valid integer score
                            continue

                return scores
            else:
                print("Error: Unexpected API response format. Missing expected fields in the response.")
                debug_print(debug, "Full API response structure:")
                debug_print(debug, json.dumps(result, indent=2))
                return {}
        else:
            print(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        sys.exit(1)


def turkish_sort_key(s):
    """
    Custom sort key function for Turkish alphabet.
    Tries to use locale if available, otherwise falls back to custom mapping.
    """
    try:
        # Try to set Turkish locale
        locale.setlocale(locale.LC_COLLATE, 'tr_TR.UTF-8')
        return locale.strxfrm(s.lower())
    except (locale.Error, AttributeError):
        # Fall back to custom Turkish character mapping if locale setting fails
        # Turkish alphabet order: a, b, c, ç, d, e, f, g, ğ, h, ı, i, j, k, l, m, n, o, ö, p, r, s, ş, t, u, ü, v, y, z
        tr_char_map = {
            'ç': 'c\u0327',  # c comes before ç
            'ğ': 'g\u0327',  # g comes before ğ
            'ı': 'i\u0326',  # ı comes before i
            'i': 'i\u0327',  # i comes after ı
            'ö': 'o\u0327',  # o comes before ö
            'ş': 's\u0327',  # s comes before ş
            'ü': 'u\u0327',  # u comes before ü
        }

        # Replace Turkish characters with their sortable equivalents
        result = ''
        for c in s.lower():
            result += tr_char_map.get(c, c)

        # Handle digits as numbers
        return [int(c) if c.isdigit() else c for c in result]


def debug_print(debug_enabled: bool, *args, **kwargs):
    """Print debug messages only if debug mode is enabled."""
    if debug_enabled:
        print(*args, **kwargs)


if __name__ == "__main__":
    main()
