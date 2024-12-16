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
        return []
