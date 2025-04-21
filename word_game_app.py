import streamlit as st
import random
import time
import pandas as pd
from nltk.corpus import wordnet as wn
from nltk.corpus import words
import nltk

# First-time downloads
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('words')

# Load dictionary
word_list = [word.lower() for word in words.words() if word.isalpha() and 4 <= len(word) <= 8]
used_words = set()

# Game state
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

def get_hint(word):
    synsets = wn.synsets(word)
    if synsets:
        syn = synsets[0]
        return f"Hint: {syn.definition()}"
    return "No hint available."

# UI
st.title("🧠 WordBlitzML – Real-Time Word Puzzle")
st.write("Guess the hidden word! Use hints if needed. Your solving time determines the word difficulty.")

if st.session_state.start_time is None:
    st.session_state.start_time = time.time()

masked_word_display = " ".join(st.session_state.masked)
st.subheader(f"Word: {masked_word_display}")

guess = st.text_input("Enter a letter or full word:")

if guess:
    guess = guess.lower()
    st.session_state.attempts += 1
    if len(guess) == 1:
        found = False
        for i, letter in enumerate(st.session_state.word):
            if letter == guess:
                st.session_state.masked[i] = guess
                found = True
        if not found:
            st.warning("Letter not in word.")
    elif guess == st.session_state.word:
        st.session_state.masked = list(st.session_state.word)

    if ''.join(st.session_state.masked) == st.session_state.word:
        time_taken = round(time.time() - st.session_state.start_time, 2)
        difficulty = "Easy" if time_taken < 10 else "Medium" if time_taken < 25 else "Hard"
        
        st.success(f"🎉 Correct! The word was '{st.session_state.word}'.")
        st.write(f"⏱️ Time taken: {time_taken} seconds")
        st.write(f"🧠 Predicted Difficulty: **{difficulty}**")
        st.write(f"📌 Attempts: {st.session_state.attempts}, Hints used: {st.session_state.hints_used}")
        
        # Reset for next word
        if st.button("Next Word"):
            st.session_state.word = random.choice([w for w in word_list if w not in used_words])
            used_words.add(st.session_state.word)
            st.session_state.masked = ['_' for _ in st.session_state.word]
            st.session_state.start_time = time.time()
            st.session_state.hints_used = 0
            st.session_state.attempts = 0
    else:
        st.info("Keep guessing!")

if st.button("🔍 Get a Hint"):
    st.session_state.hints_used += 1
    st.info(get_hint(st.session_state.word))
