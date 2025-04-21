import streamlit as st
import random
import time
import pandas as pd
import nltk
from nltk.corpus import wordnet as wn

# === Safe lazy download + guard ===
def get_valid_wordnet_words(min_len=4, max_len=10):
    try:
        wn.ensure_loaded()
        wordnet_words = set(
            lemma.name().lower()
            for syn in wn.all_synsets()
            for lemma in syn.lemmas()
        )
        return sorted({w for w in wordnet_words if w.isalpha() and min_len <= len(w) <= max_len})
    except Exception:
        nltk.download("wordnet")
        nltk.download("omw-1.4")
        st.warning("🔄 WordNet is downloading... Please **reload** the app in a few seconds.")
        st.stop()

word_list = get_valid_wordnet_words()

# === Category Emoji ===
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

# === Init Session ===
defaults = {
    'start_time': None, 'word': None, 'masked': None, 'hints_used': 0,
    'attempts': 0, 'guessed_letters': set(), 'solved_words': [],
    'solved': False
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.word is None:
    st.session_state.word = random.choice(word_list)
    st.session_state.masked = ['_' for _ in st.session_state.word]
    st.session_state.start_time = time.time()

# === UI ===
st.set_page_config(page_title="WordBlitzML", layout="centered")
st.markdown("<style>div.row-widget.stTextInput > label {font-weight:bold;}</style>", unsafe_allow_html=True)

st.title("🧠 WordBlitzML – Real-Time Word Puzzle")
st.caption("Smart hints guide you to the word!")

masked_display = " ".join(st.session_state.masked)
category_icon = get_word_category_icon(st.session_state.word)
st.subheader(f"Word: {masked_display} ({len(st.session_state.word)} letters)")
st.markdown(f"📚 **Category:** `{category_icon}`")

# === Auto Hints ===
synsets = wn.synsets(st.session_state.word)
if synsets:
    syn = synsets[0]
    st.markdown(f"📖 **Hint:** *{syn.definition()}*")

    synonyms = set()
    for s in synsets:
        for lemma in s.lemmas():
            w = lemma.name().lower().replace("_", " ")
            if w != st.session_state.word:
                synonyms.add(w)

    if st.session_state.attempts >= 2 and synonyms:
        st.markdown("🧠 **Synonyms:** " + ", ".join(sorted(synonyms)[:5]))

    if st.session_state.attempts >= 3 and syn.examples():
        st.markdown(f"💡 **Example:** *{syn.examples()[0]}*")

# === Word Bank after 5+ attempts ===
if st.session_state.attempts >= 5 and synonyms:
    word_bank = list(synonyms)
    random.shuffle(word_bank)
    chosen = word_bank[:5] + [st.session_state.word]
    random.shuffle(chosen)
    st.markdown("🔍 **Choose from these options (one is the answer!):**")
    st.write(", ".join(f"`{w}`" for w in chosen))

# === Input ===
guess = st.text_input("Enter a letter or full word:", key="guess_input_box")

if guess:
    guess = guess.lower()
    word = st.session_state.word
    st.session_state.attempts += 1

    if len(guess) == 1:
        st.session_state.guessed_letters.add(guess)
        for i, letter in enumerate(word):
            if letter == guess:
                st.session_state.masked[i] = guess
        if guess not in word:
            st.warning(f"❌ Letter '{guess}' is not in the word.")

    elif len(guess) != len(word):
        st.warning(f"⚠️ The word has **{len(word)}** letters. Try a guess of that length.")

    elif guess == word:
        st.session_state.masked = list(word)
        st.session_state.solved = True

    else:
        result_display = []
        used_positions = [False] * len(word)
        correct_positions = 0

        for i in range(len(word)):
            if guess[i] == word[i]:
                st.session_state.masked[i] = guess[i]
                result_display.append(f"🟩 **{guess[i]}**")
                used_positions[i] = True
                correct_positions += 1
            else:
                result_display.append("")

        for i in range(len(word)):
            if result_display[i] == "":
                if guess[i] in word:
                    found = False
                    for j in range(len(word)):
                        if guess[i] == word[j] and not used_positions[j]:
                            found = True
                            used_positions[j] = True
                            break
                    result_display[i] = f"🟨 **{guess[i]}**" if found else f"⬛ **{guess[i]}**"
                else:
                    result_display[i] = f"⬛ **{guess[i]}**"

        st.markdown(f"**{guess.upper()}**<br>{' '.join(result_display)}", unsafe_allow_html=True)
        st.error("🚫 Not quite! Here's your feedback:")

# === BONUS HINT BUTTON ===
if st.button("🔍 Show a Bonus Hint"):
    st.session_state.hints_used += 1
    if synsets:
        syn = synsets[0]
        hyp = syn.hypernyms()
        if hyp:
            st.info(f"🔎 **General category:** {hyp[0].lemma_names()[0]}")
        try:
            st.info(f"🧬 **Lexical file:** `{syn.lexname()}`")
        except:
            pass
        if st.session_state.word in ["shravan", "karthika"]:
            st.info("🌐 **Origin:** Sanskrit root used in Hindu lunar calendars.")

# === Guessed Letters ===
if st.session_state.guessed_letters:
    guessed = ", ".join(sorted(st.session_state.guessed_letters))
    st.caption(f"🔤 Letters guessed: {guessed}")

# === Win Condition ===
if ''.join(st.session_state.masked) == st.session_state.word or st.session_state.solved:
    time_taken = round(time.time() - st.session_state.start_time, 2)
    difficulty = "Easy" if time_taken < 10 else "Medium" if time_taken < 25 else "Hard"
    color_map = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}

    st.success(f"🎉 Correct! The word was **{st.session_state.word}**")
    st.write(f"⏱️ Time: **{time_taken}s** | 🧠 Difficulty: {color_map[difficulty]} **{difficulty}**")
    st.write(f"📌 Attempts: {st.session_state.attempts} | 🔍 Hints used: {st.session_state.hints_used}")

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
        st.session_state.solved = False
        st.session_state.pop("guess_input_box", None)
        st.rerun()

# === History ===
if st.session_state.solved_words:
    st.markdown("### 🗃️ Solved Word History")
    df = pd.DataFrame(st.session_state.solved_words)
    st.dataframe(df, use_container_width=True)
