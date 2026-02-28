import os
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import words, wordnet

# Ensure required NLTK data is downloaded
def download_nltk_data():
    """Downloads necessary NLTK datasets if they aren't already present."""
    required_data = ['wordnet', 'omw-1.4', 'words']
    for data in required_data:
        try:
            nltk.data.find(f'corpora/{data}')
        except LookupError:
            nltk.download(data, quiet=True)

# Initialize on module load
download_nltk_data()
lemmatizer = WordNetLemmatizer()

# Cache the english dictionary for fast access
_english_words_cache = None

def get_english_dictionary_words():
    """Returns a set of common English words."""
    global _english_words_cache
    if _english_words_cache is None:
        try:
            _english_words_cache = set(words.words())
        except Exception:
            _english_words_cache = set()
    return _english_words_cache

def get_lemmas(word):
    """
    Returns a set containing the original word and its lemmatized forms 
    (as a noun, verb, adjective, adverb) to aid in search matching.
    For example: "studying" -> {"studying", "study"}
    """
    word = word.lower().strip()
    if not word:
        return set()
        
    lemmas = {word}
    
    try:
        # Lemmatize across common parts of speech
        lemmas.add(lemmatizer.lemmatize(word, pos=wordnet.NOUN))
        lemmas.add(lemmatizer.lemmatize(word, pos=wordnet.VERB))
        lemmas.add(lemmatizer.lemmatize(word, pos=wordnet.ADJ))
        lemmas.add(lemmatizer.lemmatize(word, pos=wordnet.ADV))
    except Exception:
        pass # Fallback gracefully if NLTK fails
        
    return lemmas
