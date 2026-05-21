class Contact:
    """Class representing a single contact"""

    def __init__(self, name: str, phone: str):
        self._name = name
        self._phone = phone

    @property
    def name(self):
        return self._name

    @property
    def phone(self):
        return self._phone

    def __str__(self):
        return f"{self.name}: {self.phone}"