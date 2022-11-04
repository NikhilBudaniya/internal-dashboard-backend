
class History():
    def __init__(self, element, max_length=10):
        self.queue = [element]
        self.max_length = max_length

    def add(self, element):
        if len(self.queue) < self.max_length:
            self.queue.append(self.queue[-1])
        for i in range(len(self.queue)-1):
            self.queue[len(self.queue)-1-i] = self.queue[len(self.queue)-2-i]
        self.queue[0] = element

    def get(self, index=0):
        if index > len(self.queue)-1:
            return self.queue[-1]
        else:
            return self.queue[index]


    def __repr__(self):
        return str(self.queue)

if __name__ == "__main__":
    h = History([0])

    for i in range(100):
        h.add([i])
        print(h.queue)