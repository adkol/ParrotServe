import collections


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.dic = collections.OrderedDict()
        self.cached_length = 0

    def get(self, key: int) -> int:
        if key not in self.dic:
            return -1

        self.dic.move_to_end(key)
        return self.dic[key]
    
    def pop(self, key: int) -> int:
        val = self.dic[key]
        self.cached_length -= val[0]
        del self.dic[key]
        return

        if key not in self.dic:
            return 0
        val = self.dic[key]
        self.cached_length -= val[0]
        
        return val
    # (len(string), context) -> (len(tokenized), context)
    def put(self, key: int, value: int) -> list: # list of context id it had to pop
        
        if key in self.dic:
            self.dic.move_to_end(key)
        else:
            self.cached_length += value[0]

        self.dic[key] = value
        # to_remove = []
        # while self.cached_length > self.capacity :
        #     popped_hash, popped_value = self.dic.popitem(False)
        #     self.cached_length -= popped_value[0]

        #     to_remove.append(popped_value[1])
        return []


# Your LRUCache object will be instantiated and called as such:
# obj = LRUCache(capacity)
# param_1 = obj.get(key)
# obj.put(key,value)