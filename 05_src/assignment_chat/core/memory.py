# Short-term conversation memory: keeps the last few turns verbatim,
# and once there are too many, folds the older ones into a short
# summary (one extra LLM call) instead of sending the whole history
# every time. One ConversationMemory per browser session.

from core.config import MAX_TURNS_VERBATIM

SUMMARIZE_INSTRUCTION = (
    "Summarize the following zoo-chatbot conversation between a visitor "
    "and Sam the zookeeper in 3-4 sentences. Keep any concrete facts, "
    "animal names, or preferences the visitor mentioned. Just give the "
    "summary, no extra commentary."
)


class ConversationMemory:
    def __init__(self):
        self.turns = []       # {"role": ..., "content": ...}, most recent last
        self.summary = None   # summary of turns dropped from the list above

    def add_user(self, text):
        self.turns.append({"role": "user", "content": text})

    def add_assistant(self, text):
        self.turns.append({"role": "assistant", "content": text})

    def turn_limit(self):
        return MAX_TURNS_VERBATIM * 2  # 2 messages per (user, assistant) pair

    def too_long(self):
        return len(self.turns) > self.turn_limit()

    def condense(self, client=None, model=None):
        if not self.too_long():
            return

        limit = self.turn_limit()
        number_to_drop = len(self.turns) - limit
        old_turns = self.turns[:number_to_drop]
        recent_turns = self.turns[number_to_drop:]

        old_text = ""
        for turn in old_turns:
            old_text += turn["role"] + ": " + turn["content"] + "\n"
        if self.summary:
            old_text = "Summary so far:\n" + self.summary + "\n\nNewer turns to add:\n" + old_text

        new_summary = None
        if client is not None and model is not None:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SUMMARIZE_INSTRUCTION},
                        {"role": "user", "content": old_text},
                    ],
                    max_tokens=200,
                    temperature=0.2,
                )
                new_summary = response.choices[0].message.content.strip()
            except Exception:
                new_summary = None

        if new_summary is None:
            # no client, or the summarize call failed -- fall back
            # instead of crashing
            fallback = "[earlier turns of this conversation were trimmed to save space]"
            new_summary = (self.summary + " " + fallback) if self.summary else fallback

        self.summary = new_summary
        self.turns = recent_turns

    def get_context_messages(self, client=None, model=None):
        if self.too_long():
            self.condense(client=client, model=model)

        messages = []
        if self.summary:
            messages.append({
                "role": "system",
                "content": "Summary of earlier parts of this conversation: " + self.summary,
            })
        messages.extend(self.turns)
        return messages
