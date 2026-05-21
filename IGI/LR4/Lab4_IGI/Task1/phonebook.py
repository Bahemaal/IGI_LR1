import Task1.contact as contact

class PhoneBook:
    """Class representing a phone book"""

    def __init__(self):
        self.contacts = []

    def add_contact(self, cont: contact.Contact):
        self.contacts.append(cont)

    def find_by_prefix(self, prefix: str):
        return [c for c in self.contacts if c.phone.startswith(prefix)]

    def show_all(self):
        if not self.contacts:
            print("Phone book is empty.")
        for c in self.contacts:
            print(c)