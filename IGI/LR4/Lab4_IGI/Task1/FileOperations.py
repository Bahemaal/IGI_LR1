import pathlib

import Task1.phonebook as phonebook
import csv
import Task1.contact as contact
import pickle

parent = pathlib.Path(__file__).parent

def save_to_csv(phb: phonebook.PhoneBook, filename="phonebook.csv"):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for c in phb.contacts:
                writer.writerow([c.name, c.phone])
        print("Saved to CSV successfully.")
    except Exception as e:
        print("Error saving to CSV:", e)


def load_from_csv(phb: phonebook.PhoneBook, filename="phonebook.csv"):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            phb.contacts.clear()
            for row in reader:
                phb.add_contact(contact.Contact(row[0], row[1]))
        print("Loaded from CSV successfully.")
    except FileNotFoundError:
        print("CSV file not found.")
    except Exception as e:
        print("Error loading CSV:", e)


def save_to_pickle(phb: phonebook.PhoneBook, filename="phonebook.pkl"):
    try:
        with open(filename, 'wb') as file:
            pickle.dump(phb.contacts, file)
        print("Saved to Pickle successfully.")
    except Exception as e:
        print("Error saving to Pickle:", e)


def load_from_pickle(phb: phonebook.PhoneBook, filename="phonebook.pkl"):
    try:
        with open(filename, 'rb') as file:
            phb.contacts = pickle.load(file)
        print("Loaded from Pickle successfully.")
    except FileNotFoundError:
        print("Pickle file not found.")
    except Exception as e:
        print("Error loading Pickle:", e)

