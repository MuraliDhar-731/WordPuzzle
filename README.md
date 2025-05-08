# 🧠 WordBlitzML – Adaptive Word Puzzle Game

**WordBlitzML** is a daily brain-boosting puzzle game where players guess hidden words using intelligent clues.  
What makes it unique? It integrates **Reinforcement Learning** to adaptively control how and when hints are shown!

---

## 🎮 Game Features

- ✅ Difficulty selection: Easy / Medium / Hard
- 🔡 Real-time letter and word guessing
- 📚 Hints powered by WordNet (definition, synonyms, examples)
- 🧠 Adaptive hint pacing with Q-learning
- 📈 Dynamic difficulty scoring (time, hints, attempts)
- 🗃️ History tracking of solved words and performance

---

## 🤖 Machine Learning Component

WordBlitzML uses **Q-Learning** to decide whether to show:
- a synonym
- an example sentence
- or hold off on hinting

### 📊 State:
- Number of attempts
- Number of hints shown

### 🎯 Actions:
- `show_synonym`
- `show_example`
- `do_nothing`

### 🧮 Reward Function:
- `+10` for solving the word
- `+1` for a helpful letter
- `-1` for wrong guesses
- `-0.5` for showing unnecessary hints

### 🗂️ Persistence:
- Q-values are saved to `q_table.json` so the game improves hint strategies across sessions

---

## 🧪 Scoring Formula

```python
score = (time_taken * 2) + (hints_used * 10) + (attempts * 5)
