
import streamlit as st
st.set_page_config(page_title="WordBlitzML", layout="centered")

import random
import time
import pandas as pd
import nltk
from nltk.corpus import wordnet as wn
import json
import os

# === Q-Learning Setup ===
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

# === Word Setup ===
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
        st.warning("🔄 WordNet is downloading... Please reload the app.")
        st.stop()

word_list = get_valid_wordnet_words(4, 8)

# === Init Session ===
for k, v in {
    'start_time': None, 'word': None, 'masked': None,
    'attempts': 0, 'hints_used': 0, 'solved': False,
    'guessed_letters': set(), 'hints_shown': set()
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.word is None:
    st.session_state.word = random.choice(word_list)
    st.session_state.masked = ['_' for _ in st.session_state.word]
    st.session_state.start_time = time.time()

# === Live Timer + UI ===
elapsed = int(time.time() - st.session_state.start_time)
st.title("🧠 WordBlitzML – RL-Enhanced")
st.caption(f"⏱️ Time Elapsed: **{elapsed} seconds**")

masked_display = " ".join(st.session_state.masked)
st.subheader(f"Word: {masked_display} ({len(st.session_state.word)} letters)")

# === Hint Engine (Definition + RL Adaptive) ===
synsets = wn.synsets(st.session_state.word)
definition = synsets[0].definition() if synsets else "No definition available"
st.markdown(f"📖 **Definition:** *{definition}*")

# RL State and Hint Trigger
state = get_state_key(st.session_state.attempts, len(st.session_state.hints_shown))
q_table = load_q_table()
action = choose_action(state, q_table)

if action == "show_synonym" and "synonym" not in st.session_state.hints_shown:
    syns = set()
    for s in synsets:
        for lemma in s.lemmas():
            w = lemma.name().lower().replace("_", " ")
            if w != st.session_state.word:
                syns.add(w)
    if syns:
        st.markdown("🧠 **Synonyms:** " + ", ".join(list(syns)[:4]))
        st.session_state.hints_shown.add("synonym")

if action == "show_example" and "example" not in st.session_state.hints_shown:
    if synsets and synsets[0].examples():
        st.markdown(f"💡 **Example:** *{synsets[0].examples()[0]}*")
        st.session_state.hints_shown.add("example")

# === Guess Logic ===
guess = st.text_input("Enter a letter or word:")

if guess:
    st.session_state.attempts += 1
    word = st.session_state.word
    guess = guess.lower()

    if guess == word:
        st.session_state.masked = list(word)
        st.session_state.solved = True
        reward = 10
    elif len(guess) == 1:
        for i, l in enumerate(word):
            if l == guess:
                st.session_state.masked[i] = l
        reward = -0.5
    else:
        reward = -1

    # Update Q-table
    next_state = get_state_key(st.session_state.attempts, len(st.session_state.hints_shown))
    q_table = update_q_table(q_table, state, action, reward, next_state)
    save_q_table(q_table)

# === Win Section ===
if ''.join(st.session_state.masked) == st.session_state.word or st.session_state.solved:
    st.success(f"🎉 Solved: **{st.session_state.word}**")
    st.button("➡️ Next Word", on_click=lambda: st.session_state.update({
        'word': random.choice(word_list),
        'masked': None, 'start_time': time.time(),
        'attempts': 0, 'solved': False, 'guessed_letters': set(),
        'hints_used': 0, 'hints_shown': set()
    }))
