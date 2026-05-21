"""
Lab Work #4
Version: 1.0
Author: Vladislav Filipovsky
Date: 22.04.2026

Description:
Working with classes, files, regulars and other
"""

from Task1 import task1
from Task2 import task2
from Task3 import task3
from Task4 import task4
from Task5 import task5
from Task6 import task6

while True:
    print("""
Лабораторная работа №4
Выполнена студентом группы 453502
Филиповским Владиславом Вадимовичем

Задания:
1: Задание 1
2: Задание 2
3: Задание 3
4: Задание 4
5: Задание 5
6: Задание 6
Иное - выход
""")
    choice = input("Выберите опцию: ")
    match choice:
        case "1":
            task1.menu()
        case "2":
            task2.main()
        case "3":
            task3.main()
        case "4":
            task4.main()
        case "5":
            task5.main()
        case "6":
            task6.main()
        case _ :
            break

