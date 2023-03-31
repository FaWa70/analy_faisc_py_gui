import numpy as np

arr = np.random.normal(2, 1, (5, 5))

arr_up = arr[arr > 1.8]

arr_down = arr[arr < 2.2]

arr_cent = arr[(arr > 1.8) & (arr < 2.2)]

# arr_ceent2 = arr[1.8 < arr < 2.2]
# arr_cent = arr[(arr > 1.8) and (arr < 2.2)]