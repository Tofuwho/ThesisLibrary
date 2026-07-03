
# ruff: noqa: E402
print("Checking fitz...")
try:
    print("fitz OK")
except Exception as e:
    print(f"fitz Error: {e}")

print("Checking rapidfuzz...")
try:
    print("rapidfuzz OK")
except Exception as e:
    print(f"rapidfuzz Error: {e}")

print("Checking nltk...")
try:
    print("nltk OK")
except Exception as e:
    print(f"nltk Error: {e}")

from main.nlp_utils import download_nltk_data
print("Running download_nltk_data...")
download_nltk_data()
print("download_nltk_data Done")
