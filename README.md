# dungeoneer
A passion project intending to combine the rigid structure of dnd with the creativity of generative AI using agentic methods.

## Setup
1. Run `pip install -r requirements.txt`
2. You need to set environment variable `DUNGEONEER_MODEL` as the LLM you want to use:
   1. If using a Claude model, also set `ANTHROPIC_API_KEY=<your key>`
   2. If using local ollama, just set the `DUNGEONEER_MODEL` as the name of the model you want to use. More below on setup.
3. Run `python -m src.agent.chat`

## Using a free local model
To use a free local model, do the following steps:
1. run `curl -fsSL https://ollama.com/install.sh | sh` to install ollama
2. run something like `ollama pull gemma4` to get a free model from their [registry](https://ollama.com/search)
3. set the `DUNGEONEER_MODEL` as whichever model you selected

## Reference Material
I decided to utilize my own copy of the 2024 PHB for this project, incorporating the updated 2024 concepts as Python classes.

## Examples
There are story examples in the examples folder. This is what combat looks like:
![Combat](images/combat_rendering_map.png)