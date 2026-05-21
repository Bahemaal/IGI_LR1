import Task1.contact as contact

def input_contact():
    """Safe input of contact"""
    while True:
        name = input("Enter name: ").strip()
        phone = input("Enter phone: ").strip()

        if not name:
            print("Name cannot be empty.")
            continue

        if not phone.isdigit():
            print("Phone must contain only digits.")
            continue

        return contact.Contact(name, phone)