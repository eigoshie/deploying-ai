# Riverbend Zoo Chat -- Assignment 2

A Gradio chatbot with a persona: "Sam the Zookeeper," who answers
questions about animals and helps plan a zoo visit. Sam uses one OpenAI
function-calling loop to reach three services.

## Persona

Sam is a normal, down-to-earth zookeeper at a fictional zoo called
Riverbend Zoo -- not a cartoon mascot, just a friendly staff member.
The full system prompt is in `core/config.py`.

## Services

**Service 1 -- API (`services/wildlife_api.py`)**
Calls the free iNaturalist API (`/v1/taxa`, no key needed) to get real
facts about an animal a visitor names: taxonomy, conservation status,
a short description, observation count. The function just returns a
dict -- the model is the one that turns it into a sentence, and the
system prompt tells it to never paste the raw data verbatim.

**Service 2 -- Semantic search (`services/semantic_search.py`)**
Hybrid lexical + semantic search over a small dataset I made myself,
`data/animal_facts.csv` -- 120 animals (mammals, birds, reptiles,
amphibians, fish, invertebrates) with habitat, diet, conservation
status, and a fun fact each.

How I built it:
1. `data/build_dataset.py` writes the CSV. I typed the animal facts by
   hand instead of scraping a website, mainly so the file stays small
   and I didn't need internet access just to build it. The
   conservation statuses are simplified/approximate, not pulled
   straight from the IUCN Red List.
2. Each row's `description` column (name + habitat + diet + status +
   fun fact combined into one paragraph) gets embedded as one Chroma
   document.
3. `chromadb.PersistentClient` stores everything in `data/chroma_db/`,
   built automatically the first time the app runs.
4. Embedding model: OpenAI's `text-embedding-3-small` by default
   (reuses the same API key as the chat model). If there's no API key,
   it falls back to Chroma's built-in local model instead.
5. "Hybrid" part: if the visitor's question directly names an animal,
   that's checked first with a plain substring match (lexical). Then a
   vector search fills in anything else that's a good semantic match,
   which is what makes something like "what lives in the arctic" work
   even though the word "arctic" isn't a name in the dataset.

No SQLite used directly -- tabular data goes through pandas over the
CSV, per the assignment's constraints.

**Service 3 -- Function calling (`services/zoo_tools.py`)**
Three plain Python functions, no external API:
- `convert_measurement` -- weight/length unit conversions
- `plan_zoo_visit` -- checks if a visitor's time budget fits their
  exhibit wish-list
- `next_feeding_time` -- a simulated feeding schedule by animal
  category

I gave the model all five tools (these three plus the two services
above) on every turn and let it decide which one(s) to call, instead
of hard-coding which service handles which message. That felt closer
to how function calling is supposed to work.

## Guardrails

`core/guardrails.py` checks the message before it's sent to the model:
- Blocks obvious attempts to see/change the system prompt (phrases
  like "system prompt", "ignore previous instructions", etc.)
- Blocks the four restricted topics: cats, dogs, horoscopes/zodiac,
  Taylor Swift. Checked as whole words so "category" or "catfish"
  don't get caught by accident.

This is the backup layer -- the main defense is the system prompt
itself (`core/config.py`), which tells the model directly not to leak
its instructions or discuss those topics, even if asked indirectly.
The regex/keyword check just catches the obvious cases before they
even reach the model, which is faster and can't be talked out of it.

## Memory

Each browser session gets its own `ConversationMemory` object
(`core/memory.py`, stored in `gr.State`). It keeps the last
`MAX_TURNS_VERBATIM` (default 6) turns exactly as said. Once the
conversation goes over that, the oldest turns get summarized in one
extra call to the model, and only the summary + recent turns get sent
after that. This is based on the sliding-window idea from the
LangGraph memory docs linked in the assignment.

## Project layout

```
05_src/assignment_chat/
  app.py                    Gradio UI + tool-calling loop
  requirements.txt
  .env.example
  core/
    config.py               persona/system prompt, settings
    guardrails.py            prompt-leak + restricted-topic checks
    memory.py                 sliding-window memory
  services/
    wildlife_api.py          Service 1
    semantic_search.py       Service 2
    zoo_tools.py               Service 3
  data/
    build_dataset.py         generates animal_facts.csv
    animal_facts.csv         the dataset
    chroma_db/                created automatically on first run
```

## Running it

1. Install requirements (should already be in the course environment):
   `pip install -r requirements.txt`
2. Set your key: `export OPENAI_API_KEY=sk-...`
3. Run: `python app.py`, then open the local URL Gradio prints.

`data/animal_facts.csv` is already included, so you don't need to run
`build_dataset.py` unless you want to change the data.

## Notes / things I ran into

- Used OpenAI's Chat Completions API for function calling since that's
  what the assignment links to throughout.
- If the iNaturalist API is down or rate-limited, Sam is told to say
  so instead of making something up.
- Run this from a normal local folder, not one synced through Dropbox/
  OneDrive/a network drive. ChromaDB uses SQLite under the hood, and I
  hit a `disk I/O error` testing it from a mounted/synced folder --
  a regular local clone works fine.
