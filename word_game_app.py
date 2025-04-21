import streamlit as st
import random
import time
import pandas as pd
from nltk.corpus import wordnet as wn
from nltk.corpus import words
import nltk

# First-time downloads (will run only once)
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('words')

# === Load dictionary ===
word_list = [word.lower() for word in words.words() if word.isalpha() and 4 <= len(word) <= 8]
used_words = set()

# === Initialize game state ===
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

# === Hint generator ===
def get_hint(word):
    synsets = wn.synsets(word)
    if synsets:
        for syn in synsets:
            definition = syn.definition()
            if definition:
                return f"Hint: {definition} (POS: {syn.pos()})"
    return "No hint available from WordNet."

# === UI Elements ===
st.title("🧠 WordBlitzML – Real-Time Word Puzzle")
st.write("Guess the hidden word! Use hints if needed. Your solving time determines the word difficulty.")

if st.session_state.start_time is None:
    st.session_state.start_time = time.time()

# === Display the masked word ===
masked_word_display = " ".join(st.session_state.masked)
st.subheader(f"Word: {masked_word_display}")

# === User input ===
guess = st.text_input("Enter a letter or full word:")

if guess:
    guess = guess.lower()
    st.session_state.attempts += 1

    if len(guess) == 1:  # Letter guess
        st.session_state.guessed_letters.add(guess)
        found = False
        for i, letter in enumerate(st.session_state.word):
            if letter == guess:
                st.session_state.masked[i] = guess
                found = True
        if found:
            st.success(f"✅ Letter '{guess}' is in the word!")
        else:
            st.warning(f"❌ Letter '{guess}' is not in the word.")

    elif guess == st.session_state.word:  # Full word guess
        st.session_state.masked = list(st.session_state.word)

    # === Word completely guessed ===
    if ''.join(st.session_state.masked) == st.session_state.word:
        time_taken = round(time.time() - st.session_state.start_time, 2)
        difficulty = "Easy" if time_taken < 10 else "Medium" if time_taken < 25 else "Hard"

        st.success(f"🎉 Correct! The word was **'{st.session_state.word}'**.")
        st.write(f"⏱️ Time taken: **{time_taken} seconds**")
        st.write(f"🧠 Predicted Difficulty: **{difficulty}**")
        st.write(f"📌 Attempts: {st.session_state.attempts} | 🔍 Hints used: {st.session_state.hints_used}")

        if st.button("Next Word"):
            # Reset state for a new word
            st.session_state.word = random.choice([w for w in word_list if w not in used_words])
            used_words.add(st.session_state.word)
            st.session_state.masked = ['_' for _ in st.session_state.word]
            st.session_state.start_time = time.time()
            st.session_state.hints_used = 0
            st.session_state.attempts = 0
            st.session_state.guessed_letters = set()
    else:
        st.info("Keep guessing!")

# === Hint Button ===
if st.button("🔍 Get a Hint"):
    st.session_state.hints_used += 1
    st.info(get_hint(st.session_state.word))

# === Optional: Show guessed letters so far ===
if st.session_state.guessed_letters:
    guessed = ", ".join(sorted(st.session_state.guessed_letters))
    st.caption(f"🔤 Letters guessed: {guessed}")
