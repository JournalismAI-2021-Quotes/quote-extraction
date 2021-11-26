import sys
import logging
import json
import spacy

from utils.quote_extraction import extract_quotes_and_sentence_speaker

# Utility functions
def check_if_fname_exists(fname):
    import os
    return os.path.exists(fname)


def load_file(fname):
    with open(fname, 'rt') as fin:
        return fin.read()


def get_text_from_input(input_):
    """ Get text from `input` provided.
        Check if input provided is a file name. If so, load and return contents.
        Else: Assume input provided is the input text.
        Returns: text to be processed:str """
    if check_if_fname_exists(input_):
        return load_file(input_)
    else:
        return input_


# Quote extraction
def run_one(text, model_name='en_core_web_trf', debug=True):
    nlp = spacy.load(model_name)
    results = extract_quotes_and_sentence_speaker(text, nlp, debug)
    return results

def write_jsonl(data, path):
    import srsly
    srsly.write_jsonl(path, [d.to_dict() for d in data])
    logging.info(f"Output witten to {output_path}")

if __name__ == "__main__":
    output_path = './data/quotes_results.jsonl'
    try:
        inp = sys.argv[1]
    except IndexError:
        inp = input('Specify input text file.')
    text = get_text_from_input(inp)
    output, sentences = run_one(text, debug=False)
    write_jsonl(output, output_path)
