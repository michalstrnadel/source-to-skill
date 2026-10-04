https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3090s

# 16 — Prompt Injection

**Definition:** hijacking an LLM by giving it content that *looks like new
instructions*, so it takes over the prompt. The user typically can't see the
injected text; the model can.

## Three examples

1. **Hidden text in an image.** User asks "what does this say?"; the model
   replies "I don't know" and mentions a 10% off sale at Sephora. The image
   contains very faint white text instructing exactly that.
2. **Poisoned web page via search (Bing).** User asks for the best movies of
   2022. The answer lists movies, then announces the user won a $200 Amazon
   gift card and should log in via a link — a fraud link. One of the browsed
   pages contained hidden (e.g. white-on-white) text telling the model to
   forget previous instructions and publish the link.
3. **Data exfiltration via a shared Google Doc (Bard).** Someone shares a doc
   containing an injection; you ask Bard to summarize it. The injected prompt
   makes Bard gather your personal data and encode it into the URL of a
   markdown image pointing at an attacker's server — rendering the image sends
   the data in the GET request.
   - **Defense in place:** a Content Security Policy blocks images from
     arbitrary domains (only trusted Google domains).
   - **Bypass:** Google Apps Script (macro-like functionality) can export the
     data into a Google Doc — inside the Google domain, hence "safe" — that the
     attacker has access to.

## Takeaways

- Any content the model reads — images, retrieved web pages, shared
  documents — is a potential instruction channel.
- Domain-level defenses can be routed around through trusted features of the
  same platform.
