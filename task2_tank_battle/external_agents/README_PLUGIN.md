# External Student Group Algorithm Plugin Guide (Requirement 3)

This directory (`external_agents/`) is automatically scanned by the Tank Battle CLI and PyGame GUI so algorithms developed by different student groups can compete head-to-head under the exact same game environment.

## How to Add Your Group's Algorithm

Drop any `.py` file (e.g. `group_alpha_agent.py`) into `external_agents/`, or load it directly in the PyGame GUI using the **"Load External Agent (.py)"** button.

Your Python file can use **either** a Class-based or Function-based interface:

### Option A: Class-Based Agent
```python
AGENT_NAME = "GroupAlpha_TankAI"

class GroupAlphaAgent:
    def get_action(self, state) -> str:
        # `state` is a safe clone of GameState
        # Return one of: "MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT", "FIRE", "STAY"
        return "FIRE"
```

### Option B: Function-Based Agent
```python
AGENT_NAME = "GroupBeta_FuncAI"

def get_action(state) -> str:
    return "MOVE_UP"
```

*(Optional)* Set `USE_DICT_STATE = True` at the top of your file if your function prefers receiving a plain Python `dict` (`state.to_dict()`) instead of a `GameState` object.

## Safety & Fair Play Guarantees
* **State Isolation:** Every call to `get_action(state)` receives a defensive clone of the game state, so external code cannot accidentally or intentionally mutate the live board.
* **Action Validation:** Returned strings or `Action` enums are validated; invalid returns safely default to `STAY`.
