1. Follow structed 

2. Too much complicated result

3. Fix prime number (0,1 should be None, 0).

4. practicaly understand use of lock

## Review-1: Addressing Comments


### For Jobs store use list instead of dict.
1. This can be done but as per doc I should implement in dict only (refer: TR-13)
2. Also using list is bad approach. In future if we want to delete specific job we can delete in list but (waste of space alloted to list)


### Use Inheritence for validation input and output.

1. Initial comment was use diction initialised in `__init__` block.
2. created diction pointing to validation.
3. Reuse most of the feature of previous calculator functions as much as possible.
4. Use function overiding as much as possible.

