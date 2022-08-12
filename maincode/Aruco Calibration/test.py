import numpy as np

array_one = np.array([[ 1,  2,  3,  4,  5],
                      [ 5,  7,  8,  9, 10],
                      [11, 12, 13, 14, 15],
                      [16, 17, 18, 19, 20],
                      [21, 22, 23, 24, 25]])

print(array_one[:, 0])

fiveLoc = np.where(array_one[:, 0] == 5)
print(array_one[fiveLoc])