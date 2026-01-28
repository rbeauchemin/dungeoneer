class Spell:
    def __init__(self, name, casting_time, range_, components, duration, description, level=0, school=None, ability=None, cooldown=None, uses_left=None, level_requirement=1, choices=[], cast=None):
        self.name = name
        self.todo = []
        self.level = level
        self.school = school
        self.casting_time = casting_time
        self.range_ = range_
        self.components = components
        self.duration = duration
        self.description = description
        self.ability = ability
        self.cooldown = cooldown
        self.uses_left = uses_left
        self.choices = choices
        # TODO: Implement choices functionality
        if len(choices) > 0:
            self.description += " You can choose one of the following options:\n"
            for choice in choices:
                self.description += f"- {choice.name}: {choice.description}\n"
            self.cast = lambda caster: self.todo.append("Choose one of the spell's options to cast.")
        else:
            self.cast = cast


class Light(Spell):
    def __init__(self, level=0, casting_time="Action", duration="1 hour", **kwargs):
        super().__init__(
            name="Light",
            level=level,
            school="Evocation",
            casting_time=casting_time,
            range_="Touch",
            components=["V", "M (a firefly or phosphorescent moss)"],
            duration=duration,
            description="You touch one object that is no larger than 10 feet in any dimension. Until the spell ends, the object sheds bright light in a 20-foot radius and dim light for an additional 20 feet. The light can be colored as you like. Completely covering the object with something opaque blocks the light. The spell ends if you cast it again or dismiss it as an action.",
            **kwargs
        )
