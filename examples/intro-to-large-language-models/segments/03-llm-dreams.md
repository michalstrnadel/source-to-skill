https://www.youtube.com/watch?v=zjkBMFhNj_g&t=538s

# 03 — LLM dreams: what a base model generates

- **Inference loop:** sample a word, feed it back in, get the next word,
  repeat. A network trained on web pages, let loose this way, "dreams"
  internet documents.
- Examples shown: something like Java code, something like an Amazon product
  listing, something like a Wikipedia article.

## Form is right, content is uncertain

- In the product "dream", the title, author and ISBN are invented. The model
  knows an ISBN is a number of roughly a certain length after "ISBN:" and
  fills in something plausible — the number almost certainly doesn't exist.
- In the Wikipedia-like article about a fish species, the text does not
  appear verbatim in training data, yet the facts are roughly correct: the
  model has knowledge about the fish and pours it into the right form.
- **You never know which parts are memorized and which are hallucinated.**
  The model is mimicking the training distribution, producing the correct
  *form* filled with partially reliable knowledge.
