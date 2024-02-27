values = ["fish", "bat", "shark", "zombie", "48 pounds of iron ore", "oil tanker full of crude oil"]

new_list = []

for value in values:
    values.remove(value)
    new_list.append(value)
    print(values, '\n', new_list, '\n')