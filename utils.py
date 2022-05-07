import numpy as np

def date_diff_secs(start, end):
    difference = (end - start)
    return difference.total_seconds()

# class CrossCheck:
#     def __init__(self, data, data_type):
#         self.data = data
#         self.data_type = data_type
#
# class ScalarCrossCheck(CrossCheck):
#
#     def get_variance(self):
#         return np.


