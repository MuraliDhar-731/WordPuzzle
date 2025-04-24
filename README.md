## 🤔 What’s the Machine Learning in WordBlitzML?

Even though WordBlitzML doesn't use a traditional ML model like SVM or neural networks, it incorporates **core machine learning concepts** to drive intelligent behavior:

---

### 🌐 1. Difficulty Scoring Engine (Heuristic ML Logic)
We infer word difficulty dynamically using a composite scoring formula:

```python
score = (time_taken * 2) + (hints_used * 10) + (attempts * 5)
```

This functions like a rule-based regression model, where each feature contributes to an outcome:
- ⏱️ **Time Taken** = User hesitation
- ❓ **Hints Used** = Reliance on support
- 🔁 **Attempts** = Trial-and-error

The system classifies difficulty as:
- Easy < 40
- Medium 40–79
- Hard ≥ 80

This weighted formula simulates a basic regression model used in machine learning.

---

### 📊 2. Feature Engineering (Built-In)
Each session creates structured data including:
- `time_taken`
- `hints_used`
- `attempts`
- `word_category`
- `outcome`

These features are ML-ready for any future supervised or unsupervised model.
For example, you could use this dataset to train a difficulty predictor or cluster users by solving behavior.

---

### 🏠 3. Real-Time Behavioral Feedback
Hints are unlocked based on attempts, simulating **adaptive learning**, just like an AI tutor:
- Definitions are always shown
- Synonyms appear after 2 attempts
- Example usage after 3+
- Bonus hint logic mimics explainability (i.e., surfacing transparent reasoning for recommendations, as in explainable AI frameworks like LIME or Grad-CAM)

---

### 🔧 Bonus Potential
With Firebase logging or a leaderboard:
- Collect user solve time + accuracy
- Train difficulty models per user
- Implement reinforcement learning for adaptive hint pacing

---

> “WordBlitzML doesn’t just play a game — it learns how well you’re playing it.”
