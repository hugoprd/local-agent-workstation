import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Annotated
from typing_extensions import TypedDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

print(ROOT_DIR)

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.state import CompiledStateGraph

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

from ollama_workspace.agents.tools.web_search_tool import web_search, read_web_page
from ollama_workspace.agents.tools.workspace_search_tool import search_workspace_files

from logs.cmd.setup_logger import get_logger

now = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_NAME = f"orchestrator_{now}_log"
logger = get_logger(name=LOG_NAME)

CONFIG_PATH = ROOT_DIR / "ollama_workspace" / "config.json"
PROMPTS_DIR = ROOT_DIR / "ollama_workspace" / "agents" / "prompts"


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def get_or_create_config() -> dict:
    """
    reads the config.json file or creates a new one by calling the detect_model.sh script.
    """
    script_path = ROOT_DIR / "ollama_workspace" / "agents" / "utils" / "detect_model.sh"

    default_config = {"model": "", "temperature": 0.3}

    if not CONFIG_PATH.exists():
        logger.info("config.json not found. creating a new one...")

        model_name = "qwen2.5-coder:7b"  # fallback
        try:
            result = subprocess.run(
                ["bash", str(script_path)], capture_output=True, text=True, check=True
            )
            detected = result.stdout.strip()
            if detected:
                model_name = detected
                logger.info(f"model detected: {model_name}")
        except Exception as e:
            logger.warning(
                f"WARNING: failed to run detect_model.sh. using fallback.\nERROR: {e}"
            )

        default_config["model"] = model_name

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)

        return default_config

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config.get("model"):
        logger.info("model camp empty in config.json.")

        try:
            result = subprocess.run(
                ["bash", str(script_path)], capture_output=True, text=True, check=True
            )
            detected = result.stdout.strip()

            if detected:
                config["model"] = detected
                logger.info(f"Modelo preenchido via script shell: {config['model']}")

                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
        except Exception as e:
            logger.warning(f"WARNING: fail to run detect_model.sh: {e}")

    return config


def load_prompt(filename: str) -> str:
    """
    reads .txt files for prompts.
    """
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path = PROMPTS_DIR / filename

    if not prompt_path.exists():
        logger.warning(f"prompt file '{filename}' not found. using fallback.")
        return "you are a helpful AI assistant. always respond in English."

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _orchestrator_node(llm, state: AgentState):
    prompt_text = load_prompt("orchestrator_prompt.txt")
    system_instruction = SystemMessage(content=prompt_text)

    messages = [system_instruction] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response]}


def orchestrator() -> CompiledStateGraph:
    # 1. load configs
    config = get_or_create_config()

    # 2. tools list
    tools = [web_search, read_web_page, search_workspace_files]

    # 3. configuration of the Ollama model using configs.json
    llm = ChatOllama(model=config["model"], temperature=config["temperature"]).bind_tools(tools)

    # 4. Orchestrator node
    def orchestrator_wrapper(state: AgentState):
        return _orchestrator_node(llm, state)

    # 5. graph execution construction
    builder = StateGraph(AgentState)
    builder.add_node("orchestrator", orchestrator_wrapper)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges("orchestrator", tools_condition)
    builder.add_edge("tools", "orchestrator")

    return builder.compile()


def main():
    logger.info("agents orchestrator active. type 'exit' to quit\n")

    graph = orchestrator()
    chat_history = []

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        chat_history.append(("user", user_input))

        logger.info("Processing user input...")

        events = graph.stream({"messages": chat_history}, stream_mode="values")

        for i, state_update in enumerate(events):
            if i == 0:
                continue

            last_msg = state_update["messages"][-1]

            if last_msg.type == "ai":
                if last_msg.content:
                    print(f"\nORCHESTRATOR THOUGHT: {last_msg.content}\n")
                    logger.info(f"ORCHESTRATOR TEXT: {last_msg.content}")

                if getattr(last_msg, "tool_calls", None):
                    for tool_call in last_msg.tool_calls:
                        msg = (
                            f"[ACTION] turning on agent: {tool_call['name']} ",
                            f"| Args: {tool_call['args']}",
                        )
                        print(f"\n{msg}")
                        logger.info(msg)
            elif last_msg.type == "tool":
                msg = (
                    f"[CONCLUDED] tool '{last_msg.name}' ",
                    f"obtained {len(last_msg.content)} characters of data.",
                )
                print(f"{msg}")
                logger.info(msg)

        chat_history = state_update["messages"]
        print("-" * 19)


if __name__ == "__main__":
    main()
