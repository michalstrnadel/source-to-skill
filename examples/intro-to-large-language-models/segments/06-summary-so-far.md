https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1072s

# 06 — Summary so far: how to get something like ChatGPT

## Stage 1 — Pretraining (expensive, rare)

1. Download a lot of internet text.
2. Get a cluster of GPUs (special-purpose, very expensive parallel computers —
   not something you buy at Best Buy).
3. Compress the text into the network's parameters — costs on the order of a
   few million dollars. [17:52](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1072s)
4. Result: the **base model**. Done inside companies maybe once a year or
   every several months.

## Stage 2 — Fine-tuning (cheap, frequent)

1. Write labeling instructions specifying how the assistant should behave.
2. Hire people (e.g. through a company like Scale AI) to write ~100,000
   high-quality ideal Q&A responses. [18:52](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1132s)
3. Fine-tune the base model on them — maybe ~1 day instead of months. [18:52](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1132s)
4. Result: the **assistant model**.
5. Run lots of evaluations, deploy, monitor.

## The misbehavior-fixing loop

- Collect conversations where the assistant responded badly. [18:52](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1132s)
- Have a person overwrite the bad response with the correct one.
- Insert that as a training example; next fine-tune improves on that case. [19:54](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1194s)
- Because fine-tuning is cheap, companies iterate **weekly or daily** —
  much faster than on pretraining. [19:54](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1194s)

## Base vs assistant releases

- Meta released both **base** and **assistant** Llama 2 models. [19:54](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1194s)
- A base model is not directly usable for Q&A: given questions it may reply
  with more questions — it is an internet-document sampler.
- Its value: Meta already did the expensive stage 1, so you can do your own
  fine-tuning with a lot of freedom. [20:55](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1255s) Want plain Q&A? Use the assistant model.
