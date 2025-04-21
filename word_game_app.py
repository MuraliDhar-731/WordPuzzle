import streamlit as st
import random
import time
import pandas as pd
from nltk.corpus import wordnet as wn
import nltk

nltk.download('wordnet')
nltk.download('omw-1.4')

# === Load WordNet words ===
def get_valid_wordnet_words(min_len=4, max_len=8):
    wordnet_words = set(lemma.name().lower() for syn in wn.all_synsets() for lemma in syn.lemmas())
    return sorted({w for w in wordnet_words if w.isalpha() and min_len <= len(w) <= max_len})

word_list = get_valid_wordnet_words()

# === Category with emoji ===
def get_word_category_icon(word):
    synsets = wn.synsets(word)
    if not synsets:
        return "🧩 Unknown"
    syn = synsets[0]
    pos_map = {'n': "📘 Noun", 'v': "🔧 Verb", 'a': "✨ Adjective", 'r': "🏃 Adverb"}
    category = pos_map.get(syn.pos(), "🧩 Other")
    for hyp in syn.hypernyms():
        if 'container.n.01' in hyp.name() or 'vessel.n.03' in hyp.name():
            return "☕ Container"
    if 'animal.n.01' in [h.name() for h in syn.hypernyms()]:
        return "🐾 Animal"
    return category

# === Hint Ladder ===
def get_hint_ladder(word, level):
    synsets = wn.synsets(word)
    if not synsets:
        return ["No definition available."]
    hints = []
    syn = synsets[0]
    if definition := syn.definition():
        hints.append(f"📖 Definition: {definition}")
    if level >= 2:
        synonyms = set()
        for s in synsets:
            for lemma in s.lemmas():
                if lemma.name().lower() != word.lower():
                    synonyms.add(lemma.name().replace("_", " "))
        if synonyms:
            hints.append("🧠 Synonyms: " + ", ".join(sorted(synonyms)[:5]))
    if level >= 3 and (examples := syn.examples()):
        hints.append(f"💡 Example: *{examples[0]}*")
    if level >= 4 and (hypernyms := syn.hypernyms()):
        hints.append(f"🔎 General category: {hypernyms[0].lemma_names()[0]}")
    return hints

# === Init session state ===
defaults = {
    'start_time': None, 'word': None, 'masked': None, 'hints_used': 0,
    'attempts': 0, 'guessed_letters': set(), 'solved_words': [],
    'hint_requested': False, 'solved': False
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# === Start new game ===
if st.session_state.word is None:
    st.session_state.word = random.choice(word_list)
    st.session_state.masked = ['_' for _ in st.session_state.word]
    st.session_state.start_time = time.time()

# === UI Start ===
st.set_page_config(page_title="WordBlitzML", layout="centered")
st.markdown("<style>div.row-widget.stTextInput > label {font-weight:bold;}</style>", unsafe_allow_html=True)

st.title("🧠 WordBlitzML – Real-Time Word Puzzle")
st.caption("Guess the hidden word. Color-coded feedback below.")

masked_display = " ".join(st.session_state.masked)
category_icon = get_word_category_icon(st.session_state.word)
st.subheader(f"Word: {masked_display}")
st.markdown(f"📚 **Category:** `{category_icon}`")

# === Input box ===
guess = st.text_input("Enter a letter or full word:", key="guess_input_box")

# === Handle guesses ===
if guess:
    guess = guess.lower()
    st.session_state.attempts += 1
    word = st.session_state.word
    masked = st.session_state.masked

    if len(guess) == 1:
        st.session_state.guessed_letters.add(guess)
        for i, letter in enumerate(word):
            if letter == guess:
                masked[i] = guess
        if guess not in word:
            st.warning(f"❌ Letter '{guess}' is not in the word.")

    elif len(guess) == len(word):
        if guess == word:
            st.session_state.masked = list(word)
            st.session_state.solved = True
        else:
            result_display = []
            word_chars = list(word)
            used_positions = [False] * len(word)
            correct_positions = 0
            # First pass: greens
            for i in range(len(word)):
                if guess[i] == word[i]:
                    masked[i] = guess[i]
                    result_display.append(f"🟩 **{guess[i]}**")
                    used_positions[i] = True
                    correct_positions += 1
                else:
                    result_display.append("")  # placeholder

            # Second pass: yellows and blacks
            for i in range(len(word)):
                if result_display[i] == "":
                    if guess[i] in word:
                        found = False
                        for j in range(len(word)):
                            if guess[i] == word[j] and not used_positions[j]:
                                found = True
                                used_positions[j] = True
                                break
                        if found:
                            result_display[i] = f"🟨 **{guess[i]}**"
                        else:
                            result_display[i] = f"⬛ **{guess[i]}**"
                    else:
                        result_display[i] = f"⬛ **{guess[i]}**"

            st.markdown(f"**{guess.upper()}**<br>{' '.join(result_display)}", unsafe_allow_html=True)
            st.error("🚫 Not quite! Here's how you did:")

    else:
        st.warning("⚠️ Enter a single letter or a word of correct length.")

# === Hint Button ===
if st.button("🔍 Get a Hint"):
    st.session_state.hint_requested = True
    st.session_state.hints_used += 1

if st.session_state.hint_requested:
    hint_level = st.session_state.attempts
    for hint in get_hint_ladder(st.session_state.word, hint_level):
        st.info(hint)

# === Guessed Letters Display ===
if st.session_state.guessed_letters:
    guessed = ", ".join(sorted(st.session_state.guessed_letters))
    st.caption(f"🔤 Letters guessed: {guessed}")

# === On Win ===
if ''.join(st.session_state.masked) == st.session_state.word or st.session_state.solved:
    time_taken = round(time.time() - st.session_state.start_time, 2)
    difficulty = "Easy" if time_taken < 10 else "Medium" if time_taken < 25 else "Hard"
    color_map = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}

    st.success(f"🎉 Correct! The word was **{st.session_state.word}**")
    st.write(f"⏱️ Time: **{time_taken}s** | 🧠 Difficulty: {color_map[difficulty]} **{difficulty}**")
    st.write(f"📌 Attempts: {st.session_state.attempts} | 🔍 Hints: {st.session_state.hints_used}")

    if not any(w['Word'] == st.session_state.word for w in st.session_state.solved_words):
        st.session_state.solved_words.append({
            "Word": st.session_state.word,
            "Category": category_icon,
            "Time (s)": time_taken,
            "Difficulty": difficulty,
            "Attempts": st.session_state.attempts,
            "Hints Used": st.session_state.hints_used
        })

    if st.button("➡️ Next Word"):
        st.session_state.word = random.choice(word_list)
        st.session_state.masked = ['_' for _ in st.session_state.word]
        st.session_state.start_time = time.time()
        st.session_state.hints_used = 0
        st.session_state.attempts = 0
        st.session_state.guessed_letters = set()
        st.session_state.hint_requested = False
        st.session_state.solved = False
        st.session_state.pop("guess_input_box", None)
        st.experimental_rerun()

# === Word History ===
if st.session_state.solved_words:
    st.markdown("### 🗃️ Solved Word History")
    df = pd.DataFrame(st.session_state.solved_words)
    st.dataframe(df, use_container_width=True)
