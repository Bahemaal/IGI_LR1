"""
Lab Work #4
Task 2: Text Analysis using Regular Expressions
Variant 2

Description:
Reads text from file, analyzes it using regex,
saves results, and archives them.
"""
import pathlib
import re
import zipfile


# working with file

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)


# regulars

def extract_words(text):
    return re.findall(r'\b\w+\b', text)


def highlight_pairs(text):
    return re.sub(r'([a-z][A-Z])', r'_?_\1_?_', text)


def count_short_words(words):
    return len([w for w in words if len(w) < 7])


def shortest_word_a(words):
    words_a = [w for w in words if w.lower().endswith('a')]
    return min(words_a, key=len) if words_a else None


def sort_by_length(words):
    return sorted(words, key=len, reverse=True)


# tasks

def sentence_stats(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    declarative = len(re.findall(r'\.', text))
    question = len(re.findall(r'\?', text))
    exclam = len(re.findall(r'!', text))

    return len(sentences), declarative, question, exclam


def avg_word_length(words):
    return sum(len(w) for w in words) / len(words) if words else 0


def avg_sentence_length(words, sentence_count):
    return len(words) / sentence_count if sentence_count else 0


def count_smileys(text):
    pattern = r'[:;]-*[\(\)\[\]]+'
    return len(re.findall(pattern, text))


# archive

def archive_file(filename):
    zip_name = "result.zip"
    with zipfile.ZipFile(zip_name, 'w') as z:
        z.write(filename)
    return zip_name


def archive_info(zip_name):
    with zipfile.ZipFile(zip_name, 'r') as z:
        return z.namelist()



def main():
    parent = pathlib.Path(__file__).parent
    input_file = parent / "input.txt"
    output_file = parent / "result.txt"

    text = read_file(input_file)

    words = extract_words(text)
    highlighted = highlight_pairs(text)
    short_count = count_short_words(words)
    shortest_a = shortest_word_a(words)
    sorted_words = sort_by_length(words)

    sent_count, dec, ques, excl = sentence_stats(text)
    avg_w = avg_word_length(words)
    avg_s = avg_sentence_length(words, sent_count)
    smileys = count_smileys(text)

    result = f"""
--- MAIN TASK ---
Words: {words}

Highlighted text:
{highlighted}

Words with length < 7: {short_count}

Shortest word ending with 'a': {shortest_a}

Words sorted by length:
{sorted_words}

--- COMMON TASK ---
Total sentences: {sent_count}
Declarative: {dec}
Question: {ques}
Exclamatory: {excl}

Average word length: {avg_w:.2f}
Average sentence length: {avg_s:.2f}

Smileys count: {smileys}
"""

    write_file(output_file, result)

    zip_name = archive_file(output_file)
    files_in_zip = archive_info(zip_name)

    print("Analysis complete.")
    print("Archive contains:", files_in_zip)


if __name__ == "__main__":
    main()