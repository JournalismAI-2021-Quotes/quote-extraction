import copy

import prodigy
import spacy
from prodigy.components.loaders import JSONL
from prodigy.components.preprocess import add_tokens
from prodigy.util import set_hashes


def make_tasks(nlp, stream, labels):
    """Add a 'spans' key to each example, with predicted entities."""
    # Process the stream using spaCy's nlp.pipe, which yields doc objects.
    texts = ((eg["text"], eg) for eg in stream)
    for doc, eg in nlp.pipe(texts, as_tuples=True):
        task = copy.deepcopy(eg)
        spans = []
        for ent in doc.ents:
            # Continue if predicted entity is not selected in labels
            if labels and ent.label_ not in labels:
                continue
            # Create span dict for the predicted entitiy
            spans.append(
                {
                    "token_start": ent.start,
                    "token_end": ent.end - 1,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "text": ent.text,
                    "label": ent.label_,
                }
            )
        task["spans"] = spans
        # Rehash the newly created task so that hashes reflect added data
        task = set_hashes(task)
        yield task


@prodigy.recipe('quote-annotator')
def quote_annotator(dataset, model, file_path):
    nlp = spacy.load(model)
    stream = JSONL(file_path)
    stream = add_tokens(nlp, stream)
    stream = make_tasks(nlp, stream, ["Content", "Source", "Cue"])

    blocks = [{"view_id": "ner_manual"},
              {"view_id": "text_input",
               "field_rows": 3,
               "field_id": "feedback",
               "field_label": "Optional feedback",
               "field_placeholder": "Type here..."}]

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "blocks",
        "config": {
            "blocks": blocks,
            "labels": ["Content", "Source", "Cue"],
            "choice_auto_accept": False,
            "buttons": ["accept", "ignore", "undo"]}
    }
