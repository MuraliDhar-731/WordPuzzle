import streamlit as st
import random
import time
import pandas as pd
from nltk.corpus import wordnet as wn
import nltk

# First-time downloads
nltk.download('wordnet')
nltk.download('omw-1.4')

# === Load valid WordNet words ===
def get_valid_wordnet_words(min_len=4, max_len=8):
    wordnet_words = set(lemma.name().lower() for syn in wn.all_synsets() for lemma in syn.lemmas())
    return sorted({w for w in wordnet_words if w.isalpha() and min_len <= len(w) <= max_len})

word_list = get_valid_wordnet_words()

# === Get word category and detect animals ===
def get_word_category(word):
    synsets = wn.synsets(word)
    if not synsets:
        return "Unknown"
    pos_map = {'n': "Noun", 'v': "Verb", 'a': "Adjective", 'r': "Adverb"}
    pos = pos_map.get(synsets[0].pos(), "Other")

    for syn in synsets:
        if 'animal.n.01' in [h.name() for h in syn.hypernyms()]:
            return "Animal"
    return pos

# === Hint function ===
def get_hint(word):
    synsets = wn.synsets(word)
    if synsets:
        for syn in synsets:
            definition = syn.definition()
            if definition:
                return f"Hint: {definition} (POS: {syn.pos()})"
    return "No hint available from WordNet."

# === Initialize session state ===
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'word' not in st.session_state:
    st.session_state.word = random.choice(word_list)
if 'masked' not in st.session_state:
    st.session_state.masked = ['_' for _ in st.session_state.word]
if 'hints_used' not in st.session_state:
    st.session_state.hints_used = 0
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'guessed_letters' not in st.session_state:
    st.session_state.guessed_letters = set()
if 'solved_words' not in st.session_state:
    st.session_state.solved_words = []
if 'hint_requested' not in st.session_state:
    st.session_state.hint_requested = False
if 'guess_input' not in st.session_state:
    st.session_state.guess_input = ""

# === UI ===
st.title("🧠 WordBlitzML – Real-Time Word Puzzle")
st.caption("Guess the hidden word! Use hints if needed. Your solving time determines the word difficulty.")

# Start timer
if st.session_state.start_time is None:
    st.session_state.start_time = time.time()

# Display masked word
masked_word_display = " ".join(st.session_state.masked)
category = get_word_category(st.session_state.word)
st.subheader(f"Word: {masked_word_display}")
st.markdown(f"📚 **Category:** `{category}`")

# === Input field ===
guess = st.text_input("Enter a letter or full word:", key="guess_input")

if guess:
    guess = guess.lower()
    st.session_state.attempts += 1

    if len(guess) == 1:
        st.session_state.guessed_letters.add(guess)
        for i, letter in enumerate(st.session_state.word):
            if letter == guess:
                st.session_state.masked[i] = guess
        if guess not in st.session_state.word:
            st.warning(f"❌ Letter '{guess}' is not in the word.")
    elif guess == st.session_state.word:
        st.session_state.masked = list(st.session_state.word)
    else:
        st.error(f"🚫 '{guess}' is not the correct word.")

# === Win logic ===
if ''.join(st.session_state.masked) == st.session_state.word:
    time_taken = round(time.time() - st.session_state.start_time, 2)
    difficulty = "Easy" if time_taken < 10 else "Medium" if time_taken < 25 else "Hard"
    color_map = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}

    st.success(f"🎉 Correct! The word was **{st.session_state.word}**")
    st.write(f"⏱️ Time: **{time_taken} s**  |  🧠 Difficulty: {color_map[difficulty]} **{difficulty}**")
    st.write(f"📌 Attempts: {st.session_state.attempts} | 🔍 Hints: {st.session_state.hints_used}")

    # Save to solved list
    st.session_state.solved_words.append({
        "Word": st.session_state.word,
        "Category": category,
        "Time (s)": time_taken,
        "Difficulty": difficulty,
        "Attempts": st.session_state.attempts,
        "Hints Used": st.session_state.hints_used
    })

    # Next word
    if st.button("➡️ Next Word"):
        st.session_state.word = random.choice(word_list)
        st.session_state.masked = ['_' for _ in st.session_state.word]
        st.session_state.start_time = time.time()
        st.session_state.hints_used = 0
        st.session_state.attempts = 0
        st.session_state.guessed_letters = set()
        st.session_state.hint_requested = False
        st.session_state.guess_input = ""

# === Hint logic (persistent) ===
if st.button("🔍 Get a Hint"):
    if not st.session_state.hint_requested:
        st.session_state.hints_used += 1
        st.session_state.hint_requested = True

if st.session_state.hint_requested:
    st.info(get_hint(st.session_state.word))

# === Guessed letters display ===
if st.session_state.guessed_letters:
    guessed = ", ".join(sorted(st.session_state.guessed_letters))
    st.caption(f"🔤 Letters guessed: {guessed}")

# === Solved word history ===
if st.session_state.solved_words:
    st.markdown("### 🗃️ Solved Word History")
    df = pd.DataFrame(st.session_state.solved_words)
    st.dataframe(df, use_container_width=True)
