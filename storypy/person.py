



class Pronouns:
    def __init__(self, personal: str, objective: str, pessossive: str) -> None:
        self.personal = personal
        self.objective = objective
        self.pessossive = pessossive
    
    they = property(lambda s: s.personal)
    them = property(lambda s: s.objective)
    theirs = property(lambda s: s.pessossive)

    man: 'Pronouns'
    woman: 'Pronouns'
    nonbinary: 'Pronouns'
    neutral: 'Pronouns'
    nonhuman: 'Pronouns'
    @classmethod
    def parse(cls, text: str) -> 'Pronouns':
        text = text.replace(' ', '')

        if text.count('/') != 2:
            raise ValueError(f'Invalid pronouns "{text}"(should be in form of personal/objective/pessossive, AKA he/him/his)')
        return Pronouns(*text.split('/'))
    
    def __str__(self) -> str:
        return f"{self.personal}/{self.objective}/{self.pessossive}"
    def __repr__(self) -> str:
        return f"{type(self).__name__}(personal={self.personal}, objective={self.objective}, pessossive={self.pessossive})"
# Default pronouns
Pronouns.man = Pronouns('he', 'him', 'his')
Pronouns.woman = Pronouns('she', 'her', 'hers')
Pronouns.nonbinary = Pronouns('they', 'them', 'theirs')
Pronouns.neutral = Pronouns('they', 'them', 'theirs')
Pronouns.nonhuman = Pronouns('it', 'it', 'it\'s')


class GramaticalPerson:
    def __init__(self, name: str, pronouns: Pronouns) -> None:
        self.name = name
        self.pronouns = pronouns

    they = property(lambda s: s.pronouns.they)
    them = property(lambda s: s.pronouns.them)
    theirs = property(lambda s: s.pronouns.theirs)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name}, pronouns={self.pronouns!r})"

