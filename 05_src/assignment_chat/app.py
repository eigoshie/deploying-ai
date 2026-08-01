# Gradio chat app for "Sam the Zookeeper". Ties together all three
# services through one OpenAI function-calling loop:
#   Service 1 (API):       services/wildlife_api.py    -> wildlife_lookup
#   Service 2 (semantic):  services/semantic_search.py -> search_animal_facts
#   Service 3 (functions): services/zoo_tools.py        -> convert_measurement,
#                                                           plan_zoo_visit,
#                                                           next_feeding_time
#
# The model decides which tool(s) to call for a given message.
# Guardrails run before the model sees the message (core/guardrails.py).
# Each browser session gets its own memory (core/memory.py).
#
# Run: python app.py   (needs OPENAI_API_KEY set, see .env.example)

import json
import os

import gradio as gr
from openai import OpenAI

from core.config import OPENAI_API_KEY, OPENAI_MODEL, SYSTEM_PROMPT
from core.guardrails import pre_filter
from core.memory import ConversationMemory
from services.semantic_search import SEARCH_TOOL_SCHEMA, search_animal_facts
from services.wildlife_api import WILDLIFE_LOOKUP_TOOL_SCHEMA, wildlife_lookup
from services.zoo_tools import ZOO_TOOL_SCHEMAS, call_zoo_tool

ALL_TOOL_SCHEMAS = [WILDLIFE_LOOKUP_TOOL_SCHEMA, SEARCH_TOOL_SCHEMA] + ZOO_TOOL_SCHEMAS
MAX_TOOL_ITERATIONS = 4

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def run_tool(name, args):
    if name == "wildlife_lookup":
        return wildlife_lookup(**args)
    elif name == "search_animal_facts":
        return search_animal_facts(**args)
    else:
        return call_zoo_tool(name, args)


def run_tool_calling_loop(messages):
    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=ALL_TOOL_SCHEMAS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or "Sorry, I didn't quite catch that -- could you try again?"

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [tc.model_dump() for tc in message.tool_calls],
        })

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            try:
                result = run_tool(name, args)
            except Exception as exc:
                result = {"error": "Tool '" + name + "' failed: " + str(exc)}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=str),
            })

    return "I got a bit tangled up chasing that one down -- mind rephrasing your question?"


def respond(user_message, chat_history, memory_state):
    chat_history = chat_history or []
    memory_state = memory_state or ConversationMemory()

    if not user_message or not user_message.strip():
        return chat_history, memory_state, ""

    blocked_reply = pre_filter(user_message)
    if blocked_reply:
        memory_state.add_user(user_message)
        memory_state.add_assistant(blocked_reply)
        chat_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": blocked_reply},
        ]
        return chat_history, memory_state, ""

    if client is None:
        reply = "I'm not connected right now -- this app needs an OPENAI_API_KEY set before I can chat."
        chat_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        return chat_history, memory_state, ""

    memory_state.add_user(user_message)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory_state.get_context_messages(client=client, model=OPENAI_MODEL))

    try:
        reply = run_tool_calling_loop(messages)
    except Exception as exc:
        reply = "Something went wrong on my end (" + type(exc).__name__ + "). Mind trying again?"

    memory_state.add_assistant(reply)
    chat_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]
    return chat_history, memory_state, ""


def clear_conversation():
    return [], ConversationMemory()


with gr.Blocks(title="Riverbend Zoo Chat") as demo:
    gr.Markdown(
        "# Riverbend Zoo -- Chat with Sam the Zookeeper\n"
        "Ask about animals, plan your visit, or ask for unit conversions "
        "and feeding times.\n\n"
        "**Try:** *\"What lives in the arctic?\"* | "
        "*\"Tell me about capybaras\"* | "
        "*\"Convert 300 lb to kg\"* | "
        "*\"I have 90 minutes and want to see 8 exhibits, 15 min each -- does that work?\"* | "
        "*\"When do the reptiles get fed next?\"*"
    )

    chatbot = gr.Chatbot(height=480, label="Sam the Zookeeper")
    memory_state = gr.State(None)

    with gr.Row():
        msg = gr.Textbox(placeholder="Ask Sam something about the zoo...", scale=8, show_label=False)
        send_btn = gr.Button("Send", scale=1, variant="primary")

    clear_btn = gr.Button("Clear conversation")

    msg.submit(respond, [msg, chatbot, memory_state], [chatbot, memory_state, msg])
    send_btn.click(respond, [msg, chatbot, memory_state], [chatbot, memory_state, msg])
    clear_btn.click(clear_conversation, None, [chatbot, memory_state])


if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY is not set. The app will launch, but Sam won't be able to respond.")
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )
