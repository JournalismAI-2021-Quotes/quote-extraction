from typing import List, Optional, Union, Iterable
import spacy
from spacy.language import Language
from spacy.training import Example
from spacy.tokens.doc import SetEntsDefault
import copy

from prodigy.models.ner import EntityRecognizer, ensure_sentencizer
from prodigy.components.preprocess import split_sentences, add_tokens, make_raw_doc
from prodigy.components.sorters import prefer_uncertain
from prodigy.components.loaders import get_stream
from prodigy.core import recipe, Controller
from prodigy.util import set_hashes, log, split_string, get_labels, copy_nlp, color
from prodigy.util import BINARY_ATTR
from prodigy.util import INPUT_HASH_ATTR, msg
from prodigy.types import StreamType, RecipeSettingsType
from collections import Counter


@recipe(
    "quotes.teach",
    # fmt: off
    dataset=("Dataset to save annotations to", "positional", None, str),
    spacy_model=("Loadable spaCy pipeline with an entity recognizer", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    label=("Comma-separated label(s) to annotate or text file with one label per line", "option", "l", get_labels),
    exclude=("Comma-separated list of dataset IDs whose annotations to exclude", "option", "e", split_string),
    unsegmented=("Don't split sentences", "flag", "U", bool),
    # fmt: on
)
def teach(
        dataset: str,
        spacy_model: str,
        source: Union[str, Iterable[dict]],
        loader: Optional[str] = None,
        label: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        unsegmented: bool = False,
) -> RecipeSettingsType:
    """
    Collect the best possible training data for a named entity recognition
    model. Prodigy will decide which questions to ask next based on how
    uncertain the model is about a prediction.
    """
    log("RECIPE: Starting recipe quotes.teach", locals())
    stream = get_stream(
        source, loader=loader, rehash=True, dedup=True, input_key="text"
    )
    nlp = spacy.load(spacy_model)
    ensure_sentencizer(nlp)
    log(f"RECIPE: Creating EntityRecognizer using model {spacy_model}")
    model = EntityRecognizer(nlp, label=label)
    orig_nlp = copy_nlp(nlp)
    if label is not None:
        log("RECIPE: Making sure all labels are in the model", label)
        ner_labels = nlp.pipe_labels.get("ner", nlp.pipe_labels.get("beam_ner", []))
        for label_name in label:
            if label_name not in ner_labels:
                msg.info(f"Available labels in model {spacy_model}: {ner_labels}")
                msg.fail(
                    f"Can't find label '{label_name}' in model {spacy_model}",
                    "ner.teach will only show entities with one of the "
                    "specified labels. If a label is not available in the "
                    "model, Prodigy won't be able to propose entities for "
                    "annotation. To add a new label, you can pre-train "
                    "your model with examples of the new entity and load "
                    "it back in.",
                    exits=1,
                )
    predict = model
    if not unsegmented:
        stream = split_sentences(orig_nlp, stream)
    stream = prefer_uncertain(predict(stream))

    blocks = [{"view_id": "ner"},
              {"view_id": "text_input",
               "field_rows": 3,
               "field_id": "feedback",
               "field_label": "Optional feedback",
               "field_placeholder": "Type here..."}]

    return {
        "view_id": "blocks",
        "dataset": dataset,
        "stream": (eg for eg in stream),
        "exclude": exclude,
        "on_exit": print_results,
        "config": {
            "lang": nlp.lang,
            "label": ", ".join(label) if label is not None else "all",
            "blocks": blocks,
            "buttons": ["accept", "reject"],
        },
    }


@recipe(
    "quotes.manual",
    # fmt: off
    dataset=("Dataset to save annotations to", "positional", None, str),
    spacy_model=("Loadable spaCy pipeline for tokenization or blank:lang (e.g. blank:en)", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    label=("Comma-separated label(s) to annotate or text file with one label per line", "option", "l", get_labels),
    exclude=("Comma-separated list of dataset IDs whose annotations to exclude", "option", "e", split_string),
    unsegmented=("Don't split sentences", "flag", "U", bool),
    # fmt: on
)
def manual(
        dataset: str,
        spacy_model: str,
        source: Union[str, Iterable[dict]],
        loader: Optional[str] = None,
        label: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        unsegmented: bool = False,
) -> RecipeSettingsType:
    """
    Mark spans by token. Requires only a tokenizer and no entity recognizer,
    and doesn't do any active learning. The recipe will present all examples
    in order, so even examples without matches are shown. If character
    highlighting is enabled, no "tokens" are saved to the database.
    """
    log("RECIPE: Starting recipe quotes.manual", locals())
    blocks = [{"view_id": "ner_manual"},
              {"view_id": "text_input",
               "field_rows": 3,
               "field_id": "feedback",
               "field_label": "Optional feedback",
               "field_placeholder": "Type here..."}]
    nlp = spacy.load(spacy_model)
    labels = label  # comma-separated list or path to text file
    if not labels:
        labels = nlp.pipe_labels.get("ner", [])
        if not labels:
            msg.fail("No --label argument set and no labels found in model", exits=1)
        msg.text(f"Using {len(labels)} labels from model: {', '.join(labels)}")
    log(f"RECIPE: Annotating with {len(labels)} labels", labels)
    stream = get_stream(
        source,
        loader=loader,
        rehash=True,
        dedup=True,
        input_key="text",
        is_binary=False,
    )
    if not unsegmented:
        stream = split_sentences(nlp, stream)
    # Add "tokens" key to the tasks, either with words or characters
    stream = add_tokens(nlp, stream)

    return {
        "view_id": "blocks",
        "dataset": dataset,
        "stream": stream,
        "exclude": exclude,
        "on_exit": print_results,
        "before_db": None,
        "config": {
            "labels": labels,
            "exclude_by": "input",
            "auto_count_stream": True,
            "blocks": blocks,
            "buttons": ["accept", "ignore", "undo"],
        },
    }


@recipe(
    "quotes.correct",
    # fmt: off
    dataset=("Dataset to save annotations to", "positional", None, str),
    spacy_model=("Loadable spaCy pipeline with an entity recognizer", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    label=("Comma-separated label(s) to annotate or text file with one label per line", "option", "l", get_labels),
    update=("Whether to update the model during annotation", "flag", "UP", bool),
    exclude=("Comma-separated list of dataset IDs whose annotations to exclude", "option", "e", split_string),
    unsegmented=("Don't split sentences", "flag", "U", bool),
    # fmt: on
)
def correct(
        dataset: str,
        spacy_model: str,
        source: Union[str, Iterable[dict]],
        loader: Optional[str] = None,
        label: Optional[List[str]] = None,
        update: bool = False,
        exclude: Optional[List[str]] = None,
        unsegmented: bool = False,
) -> RecipeSettingsType:
    """
    Create gold data for NER by correcting a model's suggestions.
    """
    log("RECIPE: Starting recipe quotes.correct", locals())
    blocks = [{"view_id": "ner_manual"},
              {"view_id": "text_input",
               "field_rows": 3,
               "field_id": "feedback",
               "field_label": "Optional feedback",
               "field_placeholder": "Type here..."}]
    nlp = spacy.load(spacy_model)
    labels = label
    model_labels = nlp.pipe_labels.get('ner', [])
    if not labels:
        labels = model_labels
        if not labels:
            msg.fail("No --label argument set and no labels found in model", exits=1)
        msg.text(f"Using {len(labels)} labels from model: {', '.join(labels)}")
    # Check if we're annotating all labels present in the model or a subset
    no_missing = len(set(labels).intersection(set(model_labels))) == len(model_labels)
    log(f"RECIPE: Annotating with {len(labels)} labels", labels)
    stream = get_stream(
        source, loader=loader, rehash=True, dedup=True, input_key="text"
    )
    if not unsegmented:
        stream = split_sentences(nlp, stream)
    stream = add_tokens(nlp, stream)

    def make_tasks(nlp: Language, stream: StreamType) -> StreamType:
        """Add a 'spans' key to each example, with predicted entities."""
        texts = ((eg["text"], eg) for eg in stream)
        for doc, eg in nlp.pipe(texts, as_tuples=True, batch_size=10):
            task = copy.deepcopy(eg)
            spans = []
            for ent in doc.ents:
                if labels and ent.label_ not in labels:
                    continue
                spans.append(
                    {
                        "token_start": ent.start,
                        "token_end": ent.end - 1,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "text": ent.text,
                        "label": ent.label_,
                        "source": spacy_model,
                        "input_hash": eg[INPUT_HASH_ATTR],
                    }
                )
            task["spans"] = spans
            task[BINARY_ATTR] = False
            task = set_hashes(task)
            yield task

    def make_update(answers: Iterable[dict]) -> None:
        log(f"RECIPE: Updating model with {len(answers)} answers")
        examples = []
        for eg in answers:
            if eg["answer"] == "accept":
                doc = make_raw_doc(nlp, eg)
                ref = make_raw_doc(nlp, eg)
                spans = [
                    doc.char_span(span["start"], span["end"], label=span["label"])
                    for span in eg.get("spans", [])
                ]
                value = SetEntsDefault.outside if no_missing else SetEntsDefault.missing
                ref.set_ents(spans, default=value)
                examples.append(Example(doc, ref))
        nlp.update(examples)

    stream = make_tasks(nlp, stream)

    return {
        "view_id": "blocks",
        "dataset": dataset,
        "stream": stream,
        "update": make_update if update else None,
        "exclude": exclude,
        "config": {
            "labels": labels,
            "on_exit": print_results,
            "exclude_by": "input",
            "auto_count_stream": not update,
            "blocks": blocks,
            "buttons": ["accept", "ignore", "undo"],
        },
    }


@recipe(
    "quotes.mark",
    # fmt: off
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    label=("Comma-separated label(s) to annotate or text file with one label per line", "option", "l", get_labels),
    exclude=("Comma-separated list of dataset IDs whose annotations to exclude", "option", "e", split_string),
    # fmt :on
)
def mark(
        dataset: str,
        source: Union[str, Iterable[dict]],
        label: Optional[List[str]] = None,
        loader: Optional[str] = None,
        exclude: Optional[List[str]] = None,
) -> RecipeSettingsType:
    """
    Click through and correct pre-annotated examples, with no model in
    the loop.
    """
    log("RECIPE: Starting recipe quotes.mark", locals())
    blocks = [{"view_id": "ner_manual"},
              {"view_id": "text_input",
               "field_rows": 3,
               "field_id": "feedback",
               "field_label": "Optional feedback",
               "field_placeholder": "Type here..."}]
    stream = get_stream(source, loader=loader)

    # TODO add feedback to display?
    def ask_questions(stream: StreamType) -> StreamType:
        for eg in stream:
            if label:
                eg["label"] = label[0]
            yield eg

    # Add label or label set to config if available
    config = {"auto_count_stream": True}
    if label and len(label) == 1:
        config["label"] = label[0]
    elif label and len(label) > 1:
        config["labels"] = label
    config["blocks"] = blocks
    config["buttons"] = ["accept", "reject", "ignore"]

    return {
        "view_id": "blocks",
        "dataset": dataset,
        "stream": ask_questions(stream),
        "exclude": exclude,
        "on_exit": print_results,
        "config": config,
    }


def print_results(ctrl: Controller) -> None:
    examples = ctrl.db.get_dataset(ctrl.session_id)
    if examples:
        counts = Counter()
        for eg in examples:
            counts[eg["answer"]] += 1
        for key in ["accept", "reject", "ignore"]:
            if key in counts:
                msg.row([key.title(), color(round(counts[key]), key)], widths=10)
