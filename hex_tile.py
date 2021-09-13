class HexTile:

    def __init__(self, edges:list):
        self.edges = edges


    def __iter__(self):
        return iter(self.edges)


    def __eq__(self, other):
        if (isinstance(other, HexTile)):
            return self.edges == other.edges


    def __str__(self):
        return "<HexTile: {}>".format(self.edges)


    def __repr__(self):
        return str(self)


    def get_rotations(self) -> list:
        """Generates a list of all posible rotations of the tile"""
        rotations = []
        for i in range(6):
            rotations.append(tuple(self.edges[i:] + self.edges[:i]))
        rotations = list(set(rotations))    # Remove duplicate rotations
        return [HexTile(list(edges)) for edges in rotations]
