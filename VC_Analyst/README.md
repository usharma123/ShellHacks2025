## YC in your pocket

This refactor wraps the existing `StartupFramework` into a Google ADK agent and also recreates the original agents (market, product, founder, vc_scout, integration) as standalone ADK agents. All ADK agents are exposed via FastAPI apps.

### Layout

```
refactor/
  README.md
  requirements.txt
  startup_agent/
    __init__.py
    agent.py           # defines root_agent
    main.py            # FastAPI app using ADK helpers
    tools.py           # ADK tool wrappers over StartupFramework
    .env.example
  adk_agents/
    __init__.py
    main.py            # FastAPI app serving all agents in this folder
    market_agent/
      __init__.py
      agent.py
      tools.py
    product_agent/
      __init__.py
      agent.py
      tools.py
    founder_agent/
      __init__.py
      agent.py
      tools.py
    vc_scout_agent/
      __init__.py
      agent.py
      tools.py
    integration_agent/
      __init__.py
      agent.py
      tools.py
```

### Quickstart (local)

1. Create a virtualenv and install deps:

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r refactor/requirements.txt
```

2. Copy `.env.example` to `.env` (in `refactor/startup_agent/` or project root) and set keys.

3. Run the single aggregated agent (framework wrapper):

```
uvicorn refactor.startup_agent.main:app --host 0.0.0.0 --port 8080
```

4. Run the multi-agent ADK server (serves market/product/founder/vc_scout/integration):

```
uvicorn refactor.adk_agents.main:app --host 0.0.0.0 --port 8081
```

### Notes

- Each ADK agent exposes tools that mirror the corresponding class in `agents/` and returns pydantic models as plain dicts.
- The founder agent requires the model file `models/neural_network.keras` and RandomForest/encoder are used by VCScout; ensure the `models/` folder remains in place.
- For A2A integration, the FastAPI apps are created using ADK's FastAPI helper, which exposes agent discovery and task routes.


