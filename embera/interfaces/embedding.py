

__all__ = ["Embedding"]

class Embedding(dict):

    source_id = None
    target_id = None
    properties = {}

    def __init__(self, source, target, embedding, **properties):
        super(Embedding,self).__init__(embedding)

        if isinstance(source,int):
            self.source_id = source
        else:
            if hasattr(source, 'edges'): source = source.edges()
            elif hasattr(source, 'quadratic'): source = source.quadratic.keys()
            else: source = sorted((tuple(sorted(e)) for e in source))
            self.source_id = hash(tuple(source))

        if isinstance(target,int):
            self.target_id = target
        else:
            if hasattr(target, 'edges'): target = target.edges()
            else: target = sorted((tuple(sorted(e)) for e in target))
            self.target_id = hash(tuple(target))

        self.properties.update(properties)

    def chain_histogram(self):
        # Based on dwavesystems/minorminer quality_key by Boothby, K.
        sizes = [len(c) for c in self.values()]
        hist = {}
        for s in sizes:
            hist[s] = 1 + hist.get(s, 0)
        return hist

    def interactions_histogram(self, source, target):
        if hasattr(source, 'edges'): source = source.edges()
        elif hasattr(source, 'quadratic'): source = source.quadratic.keys()
        else: source = sorted((tuple(sorted(e)) for e in source))

        if hasattr(target, 'edges'): target = target.edges()
        else: target = sorted((tuple(sorted(e)) for e in target))

        source_id = hash(tuple(source))
        assert(self.source_id==source_id), "Source ID does not match."

        target_id = hash(tuple(target))
        assert(self.target_id==target_id), "Target ID does not match."
        interactions = {}
        for u, v in source:
            source_edge = tuple(sorted((u,v)))
            edge_interactions = []
            for s in self[u]:
                for t in self[v]:
                    target_edge = tuple(sorted((s,t)))
                    if target_edge in target:
                        edge_interactions.append(target_edge)
            interactions[(u,v)] = edge_interactions

        sizes = [len(i) for i in interactions.values()]
        hist = {}
        for s in sizes:
            hist[s] = 1 + hist.get(s, 0)
        return hist

    @property
    def max_chain(self):
        hist = self.quality_key
        return hist.pop()

    @property
    def total_qubits(self):
        QK = self.quality_key
        return sum([QK[i]*QK[i+1] for i in range(0,len(QK),2)])

    @property
    def quality_key(self):
        #TEMP: Can be better
        hist = self.chain_histogram()
        return [value for item in sorted(hist.items(), reverse=True) for value in item]

    @property
    def id(self):
        # To create a unique ID we use the quality key as an ID string...
        if not self: quality_id = "EMPTY" # ..., unless empty,
        else: quality_id = "".join([str(v) for v in self.quality_key])
        # ...and the last 8 digits of this object's hash.
        hash_id = f"{self.__hash__():08}"[-8:]
        return f"{quality_id}_{hash_id}"

    def __embedding_key(self):
        return tuple((k,tuple(self[k])) for k in sorted(self))

    def __key(self):
        return (self.source_id, self.target_id, self.__embedding_key())

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return self.__key() == other.__key()
    def __ne__(self, other):
        return self.__key() != other.__key()
    def __lt__(self, other):
        return self.quality_key < other.quality_key
    def __le__(self, other):
        return self.quality_key <= other.quality_key
    def __gt__(self, other):
        return self.quality_key > other.quality_key
    def __ge__(self, other):
        return self.quality_key >= other.quality_key
