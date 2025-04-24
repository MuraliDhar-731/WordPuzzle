import streamlit as st
st.set_page_config(page_title="WordBlitzML", layout="centered")

import random
import time
import pandas as pd
import nltk
from nltk.corpus import wordnet as wn
import json
import os

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

# === Q-Learning Setup for Hint Pacing ===
Q_FILE = "q_table.json"
ACTIONS = ["do_nothing", "show_synonym", "show_example"]
ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.2

def load_q_table():
    if os.path.exists(Q_FILE):
        with open(Q_FILE, "r") as f:
            return json.load(f)
    return {}

def save_q_table(q):
    with open(Q_FILE, "w") as f:
        json.dump(q, f)

def get_state_key(attempts, hints_shown):
    return f"{attempts}_{hints_shown}"

def choose_action(state, q):
    if state not in q:
        q[state] = {a: 0 for a in ACTIONS}
    if random.random() < EPSILON:
        return random.choice(ACTIONS)
    return max(q[state], key=q[state].get)

def update_q_table(q, state, action, reward, next_state):
    if next_state not in q:
        q[next_state] = {a: 0 for a in ACTIONS}
    old_value = q[state][action]
    next_max = max(q[next_state].values())
    q[state][action] = old_value + ALPHA * (reward + GAMMA * next_max - old_value)
    return q


# === Difficulty Mode Selector ===
st.sidebar.title("🎮 Select Difficulty")
mode = st.sidebar.radio("Choose your challenge level:", ["Easy", "Medium", "Hard"])

# Word length per difficulty
if mode == "Easy":
    min_len, max_len = 4, 5
elif mode == "Medium":
    min_len, max_len = 6, 7
else:
    min_len, max_len = 8, 10

word_list = get_valid_wordnet_words(min_len, max_len)

# === Category Icon
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

# === Init Session State ===
for key, val in {
    'start_time': None, 'word': None, 'masked': None, 'hints_used': 0,
    'attempts': 0, 'guessed_letters': set(), 'solved_words': [],
    'solved': False, 'hints_shown': set()
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.word is None:
    st.session_state.word = random.choice(word_list)
    st.session_state.masked = ['_' for _ in st.session_state.word]
    st.session_state.start_time = time.time()

# === Header UI ===
st.title("🧠WORD PUZZLE - A DAILY COMPANION FOR A NEW WORD")
elapsed_time = int(time.time() - st.session_state.start_time)
st.caption(f"⏱️ Time Elapsed: **{elapsed_time} seconds** – Smart hints guide you to the word!")

masked_display = " ".join(st.session_state.masked)
category_icon = get_word_category_icon(st.session_state.word)
st.subheader(f"Word: {masked_display} ({len(st.session_state.word)} letters)")
st.markdown(f"📚 **Category:** `{category_icon}`")


# === RL Adaptive Hint Pacing ===
synsets = wn.synsets(st.session_state.word)
definition = synsets[0].definition() if synsets else "No definition available"
st.markdown(f"📖 **Hint:** *{definition}*")

synonyms = set()
examples = []
if synsets:
    for s in synsets:
        for lemma in s.lemmas():
            word = lemma.name().lower().replace("_", " ")
            if word != st.session_state.word:
                synonyms.add(word)
        examples.extend(s.examples())

# Determine RL state and action
q_table = load_q_table()
state = get_state_key(st.session_state.attempts, len(st.session_state.hints_shown))
action = choose_action(state, q_table)

# Take RL hint action
if action == "show_synonym" and "synonym" not in st.session_state.hints_shown and synonyms:
    st.markdown("🧠 **Synonyms:** " + ", ".join(sorted(synonyms)[:5]))
    st.session_state.hints_shown.add("synonym")

if action == "show_example" and "example" not in st.session_state.hints_shown and examples:
    st.markdown(f"💡 **Example:** *{examples[0]}*")
    st.session_state.hints_shown.add("example")

# Word Bank (unchanged logic)
if st.session_state.attempts >= 5 and synonyms:
    word_bank = list(synonyms)
    random.shuffle(word_bank)
    chosen = word_bank[:5] + [st.session_state.word]
    random.shuffle(chosen)
    st.markdown("🔍 **Choose from these options (one is the answer!):**")
    st.write(", ".join(f"`{w}`" for w in chosen))


guess = st.text_input("Enter a letter or full word:", key="guess_input_box")

if guess:
    guess = guess.lower()
    word = st.session_state.word
    st.session_state.attempts += 1

    # === Reward system ===
    reward = -1  # penalty for each interaction by default

    if len(guess) == 1:
        st.session_state.guessed_letters.add(guess)
        found = False
        for i, letter in enumerate(word):
            if letter == guess:
                st.session_state.masked[i] = guess
                found = True
        if found:
            reward = +1
        else:
            st.warning(f"❌ Letter '{guess}' is not in the word.")

    elif len(guess) != len(word):
        st.warning(f"⚠️ The word has **{len(word)}** letters. Try a guess of that length.")
    elif guess == word:
        st.session_state.masked = list(word)
        st.session_state.solved = True
        reward = +10  # successful solve
    else:
        # Word-level guess with partial feedback
        result_display = []
        used_positions = [False] * len(word)
        for i in range(len(word)):
            if guess[i] == word[i]:
                st.session_state.masked[i] = guess[i]
                result_display.append(f"🟩 **{guess[i]}**")
                used_positions[i] = True
            else:
                result_display.append("")
        for i in range(len(word)):
            if result_display[i] == "":
                if guess[i] in word:
                    found = False
                    for j in range(len(word)):
                        if guess[i] == word[j] and not used_positions[j]:
                            used_positions[j] = True
                            found = True
                            break
                    result_display[i] = f"🟨 **{guess[i]}**" if found else f"⬛ **{guess[i]}**"
                else:
                    result_display[i] = f"⬛ **{guess[i]}**"
        st.markdown(f"**{guess.upper()}**<br>{' '.join(result_display)}", unsafe_allow_html=True)
        st.error("🚫 Not quite! Here's your feedback:")

    # === RL Q-Update ===
    next_state = get_state_key(st.session_state.attempts, len(st.session_state.hints_shown))
    q_table = update_q_table(q_table, state, action, reward, next_state)
    save_q_table(q_table)


# === Guessed Letters ===
if st.session_state.guessed_letters:
    guessed = ", ".join(sorted(st.session_state.guessed_letters))
    st.caption(f"🔤 Letters guessed: {guessed}")

# === Win Condition ===
if ''.join(st.session_state.masked) == st.session_state.word or st.session_state.solved:
    time_taken = round(time.time() - st.session_state.start_time, 2)

    # Composite Difficulty Score
    score = (
        time_taken * 1 +
        st.session_state.hints_used * 2 +
        st.session_state.attempts * 3
    )

    if score < 40:
        difficulty = "Easy"
    elif score < 80:
        difficulty = "Medium"
    else:
        difficulty = "Hard"

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
        st.session_state.hints_shown = set()
        st.session_state.pop("guess_input_box", None)
        st.rerun()

# === History ===
if st.session_state.solved_words:
    st.markdown("### 🗃️ Solved Word History")
    df = pd.DataFrame(st.session_state.solved_words)
    st.dataframe(df, use_container_width=True)
