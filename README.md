# dungeoneer
A passion project intending to combine the rigid structure of dnd with the creativity of generative AI using agentic methods.

## Initial Setup Option A - Docker
This build has some caveats. If you are using Claude, this will be fast to setup and fast to use. If using open source models, your docker needs to have a fair bit of memory or some GPU or it will be quite slow.
1. (Optional) Create a `.env` file and set `ANTHROPIC_API_KEY` key if you want to use Claude, and set `DUNGEONEER_MODEL` as the LLM you want to use. Defaults to download and use open source Gemma4.
2. `docker build -t dungeoneer . && docker run --rm -it -p 8000:8000 --name dungeoneer dungeoneer`

## Initial Setup Option B - Local
This is a little harder to build, but I've found it's much faster on my machine with open source models as it will use available GPU and RAM.
1. Run `pip install -r requirements.txt`
2. You need to set environment variable `DUNGEONEER_MODEL` as the LLM you want to use:
   1. If using a paid Claude model, also set `ANTHROPIC_API_KEY=<your key>`
   2. If you want to use a free Ollama model, just set the `DUNGEONEER_MODEL` as the name of the model you want to use. You can install a free model by running `curl -fsSL https://ollama.com/install.sh | sh` to install ollama and then running something like `ollama pull gemma4` to get a free model from their [registry](https://ollama.com/search)
3. If you wish to store separate campaigns in a unified frontend, run `uvicorn src.agent.server:app --reload --port 8000` and then navigate your browser to `localhost:8000`
4. If you prefer a terminal experience, for a single campaign, run `python -m src.agent.chat`

## Examples
This is how the application looks:
![Frontend](images/chat_frontend.png)

There are story examples in the examples folder.

This is what the terminal-based combat experience looks like:
![Combat](images/combat_rendering_map.png)

## Contributing
I am happy to take on contributions! The species and classes still need a lot of work in making sure they are set up correctly. I haven't even started on Subclasses.

## Reference Material
I decided to utilize my own copy of the 2024 PHB for this project, incorporating the updated 2024 concepts as Python classes.