# https://leetcode.com/problems/two-sum/description/
class Solution(object):
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        position_dict = {}
        for i, n in enumerate(nums):
            complement = target - n
            if complement in position_dict:
                return [position_dict[complement], i]
            position_dict[n] = i
        return

#print(Solution().twoSum(nums=[2, 7, 11, 15], target=9))
#print(Solution().twoSum(nums=[2, 7, 11, 15], target=18))
#print(Solution().twoSum(nums=[2, 7, 11, 15], target=22))
