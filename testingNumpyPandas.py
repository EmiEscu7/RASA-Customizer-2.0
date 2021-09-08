import csv 
from math import sqrt

conjunto = []
example = []

with open('examples_personalities.csv') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=';',quoting=csv.QUOTE_NONNUMERIC)
    line_count = 0

    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            for i in range(len(row)):
                example.append(row[i])
            conjunto.append(example)
            example = []
  

def dist_euclidea(p,q) -> float:
        return sqrt(sum((px - qx) ** 2.0 for px, qx in zip(p, q)))
a = [1,2,3]
b = [4,5,6]
print(dist_euclidea(a,b))