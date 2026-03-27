from src.creatures import Character


def handle_todo(character: Character):
    """Pop the last todo off the character's todo stack and prompt the user to resolve it.

    Todo items are either:
      - str: displayed as-is, no input required
      - dict with keys:
          "Text"    : str  - prompt shown to the user
          "Options" : list - available choices
          "Function": callable(character, choices) - called with the selected options
          "Choices" : int  (optional, default 1) - number of selections the user must make
    """
    if not character.todo:
        print("No pending todos.")
        return

    todo = character.todo.pop()

    if isinstance(todo, str):
        print(todo)
        return

    text = todo["Text"]
    options = todo["Options"]
    func = todo["Function"]
    num_choices = todo.get("Choices", 1)
    allow_same = todo.get("AllowSame", False)

    print(f"\n{text}")
    print()
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print()

    selected = []
    for n in range(num_choices):
        prompt = f"Choice {n + 1} of {num_choices}" if num_choices > 1 else "Choice"
        while True:
            raw = input(f"{prompt} (1-{len(options)}): ").strip()
            try:
                idx = int(raw) - 1
            except ValueError:
                print(f"  Enter a number between 1 and {len(options)}.")
                continue
            if not (0 <= idx < len(options)):
                print(f"  Enter a number between 1 and {len(options)}.")
                continue
            choice = options[idx]
            if choice in selected and not allow_same:
                print(f"  '{choice}' is already selected. Pick a different option.")
                continue
            selected.append(choice)
            break

    try:
        func(character, selected)
    except Exception as e:
        print(f"Error processing todo choice: {e}")
        print("Please resolve this issue then try again.")
        # Add back the popped todo to top of stack so it can be resolved after the issue is fixed
        character.todo.append(todo)
