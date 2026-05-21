"""
Lab Work #4
Title: Phone Book with File Serialization (CSV, Pickle)
Version: 1.0
Author: Vladislav Filipovsky
Date: 22.04.2026

Description:
This program implements a phone book using classes.
It supports saving/loading data using CSV and Pickle,
searching contacts by phone prefix, and user interaction.
"""

import Task1.FileOperations as FO
import Task1.phonebook as phonebook
import Task1.input as inp


def menu():
    phb = phonebook.PhoneBook()

    while True:
        print("\n===== PHONE BOOK MENU =====")
        print("1. Add contact")
        print("2. Show all contacts")
        print("3. Find by phone prefix")
        print("4. Save to CSV")
        print("5. Load from CSV")
        print("6. Save to Pickle")
        print("7. Load from Pickle")
        print("0. Exit")

        choice = input("Choose option: ")

        try:
            if choice == '1':
                contact = inp.input_contact()
                phb.add_contact(contact)

            elif choice == '2':
                phb.show_all()

            elif choice == '3':
                prefix = input("Enter phone prefix: ")
                result = phb.find_by_prefix(prefix)
                if result:
                    for c in result:
                        print(c)
                else:
                    print("No matches found.")

            elif choice == '4':
                FO.save_to_csv(phb)

            elif choice == '5':
                FO.load_from_csv(phb)

            elif choice == '6':
                FO.save_to_pickle(phb)

            elif choice == '7':
                FO.load_from_pickle(phb)

            elif choice == '0':
                print("Exiting program...")
                break

            else:
                print("Invalid choice.")

        except Exception as e:
            print("Unexpected error:", e)



if __name__ == "__main__":
    menu()