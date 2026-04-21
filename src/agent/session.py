"""GameSession — thread-based wrapper that runs Combat.run() in the background.

The combat engine is driven by stdin/stdout (``input()`` / ``print()``).
GameSession intercepts both so an agent can send commands programmatically
and receive the resulting output as strings.

Thread model
------------
``combat.run()`` executes in a daemon thread.  The main thread communicates
through two primitives:

* ``_cmd_q``     – ``Queue[str]`` carrying commands from agent → game thread.
* ``_out_buf``   – ``list[str]`` accumulating game output (protected by a lock).
* ``_waiting_evt`` – ``Event`` that is set whenever the game thread is blocked
  on ``input()``, i.e. waiting for the next player command.
* ``_done_evt``  – ``Event`` set when ``combat.run()`` returns.
"""

from __future__ import annotations

import builtins
import queue
import sys
import threading
from typing import Optional


class GameSession:
    """Drives a ``Combat`` instance programmatically via a background thread."""

    def __init__(self, combat) -> None:
        self.combat = combat
        self.winner: Optional[str] = None

        self._cmd_q: queue.Queue[str] = queue.Queue()
        self._out_lock = threading.Lock()
        self._out_buf: list[str] = []

        # Signalling events
        self._waiting_evt = threading.Event()  # set when game needs input
        self._done_evt = threading.Event()     # set when game is over

        self._thread = threading.Thread(
            target=self._run, daemon=True, name="dungeoneer-combat"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def is_game_over(self) -> bool:
        return self._done_evt.is_set()

    @property
    def awaiting_input(self) -> bool:
        return self._waiting_evt.is_set() and not self._done_evt.is_set()

    def start(self) -> str:
        """Start the combat thread. Returns all output up to the first player prompt."""
        self._thread.start()
        self._waiting_evt.wait(timeout=15)
        return self._take_output()

    def send(self, command: str) -> str:
        """Send one command to the game.

        Blocks until the game is waiting for the *next* command (or ends),
        then returns all output generated in between.
        """
        if self._done_evt.is_set():
            return f"[Game over — {self.winner} won]"

        self._waiting_evt.clear()
        self._cmd_q.put(command)

        # Wait for the game to want the next command, or finish entirely
        while not self._waiting_evt.wait(timeout=0.5):
            if self._done_evt.is_set():
                break

        return self._take_output()

    def get_map_dict(self, z: int = 0):
        """Return the map state as a JSON-serializable dict, or None if unavailable."""
        m = getattr(self.combat, "map", None)
        if m is None:
            return None
        return m.to_dict(z)

    def get_state_description(self) -> str:
        """Return a plain-text snapshot of current combat state for the agent."""
        from src.combat import _is_dead  # avoid circular import at module level

        combat = self.combat
        lines: list[str] = ["=== COMBAT STATE ==="]

        lines.append("\n[Players]")
        for p in combat.players:
            x, y, _z = p.position
            hp_str = f"{p.current_hp}/{p.max_hp} HP"
            conds = [getattr(e, "name", str(e)) for e in p.active_effects]
            cond_str = f"  [{', '.join(conds)}]" if conds else ""
            resource_str = (
                f"  actions={p.actions_left}"
                f"  bonus={p.bonus_actions_left}"
                f"  speed={p.speed}ft"
            )
            lines.append(f"  {p.name}: {hp_str}  pos=({x},{y}){cond_str}{resource_str}")

        alive = [m for m in combat.monsters if not _is_dead(m)]
        lines.append(f"\n[Enemies — {len(alive)} alive]")
        if not alive:
            lines.append("  (none — victory!)")
        for m in alive:
            x, y, _z = m.position
            hp_str = f"{m.current_hp}/{m.max_hp} HP"
            conds = [getattr(e, "name", str(e)) for e in m.active_effects]
            cond_str = f"  [{', '.join(conds)}]" if conds else ""
            lines.append(f"  {m.name}: {hp_str}  pos=({x},{y}){cond_str}")

        if self.is_game_over:
            lines.append(f"\n[GAME OVER — {self.winner} won]")

        return "\n".join(lines)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _take_output(self) -> str:
        """Drain and return all buffered output lines."""
        with self._out_lock:
            result = "".join(self._out_buf)
            self._out_buf.clear()
        return result

    def _run(self) -> None:
        """Execute combat.run() with patched stdin and stdout."""
        orig_input = builtins.input
        orig_stdout = sys.stdout

        session = self  # closure reference
        game_thread_id = threading.current_thread().ident

        class _ThreadAwareCapture:
            """Route writes: game thread → capture buffer; other threads → real stdout."""

            def write(self, text: str) -> None:
                if threading.current_thread().ident == game_thread_id:
                    with session._out_lock:
                        session._out_buf.append(text)
                else:
                    orig_stdout.write(text)

            def flush(self) -> None:
                orig_stdout.flush()

            def isatty(self) -> bool:
                return False

            @property
            def encoding(self) -> str:
                return getattr(orig_stdout, "encoding", "utf-8")

        def _patched_input(prompt: str = "") -> str:
            if threading.current_thread().ident == game_thread_id:
                # Game thread waiting for a player command
                if prompt:
                    with session._out_lock:
                        session._out_buf.append(str(prompt))
                session._waiting_evt.set()
                return session._cmd_q.get()
            # Any other thread (e.g. the main chat loop) uses real input
            return orig_input(prompt)

        sys.stdout = _ThreadAwareCapture()
        builtins.input = _patched_input

        try:
            self.winner = self.combat.run()
        except Exception as exc:
            with self._out_lock:
                self._out_buf.append(f"\n[COMBAT ERROR: {exc}]\n")
        finally:
            sys.stdout = orig_stdout
            builtins.input = orig_input
            # Always unblock any waiting send() and mark game done
            self._waiting_evt.set()
            self._done_evt.set()
