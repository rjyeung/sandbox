# https://leetcode.com/problems/contains-duplicate/description/
class Solution(object):
    def containsDuplicate(self, nums):
        """
        :type nums: List[int]
        :rtype: bool
        """
        nums_set = set(nums)
        if len(nums_set) < len(nums):
            return True
        else:
            return False
