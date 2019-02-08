from pyFEM.primitives import *
from pyFEM.classtools import Collection


class Materials(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, label, modulus):
        _material = Material(label, modulus)
        Collection.add(self, _material)

        return _material


class Sections(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, label, material, area):
        _section = Section(label, self.parent.materials[material], area)
        Collection.add(self, _section)

        return _section


class Nodes(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, label, x, y, z):
        _node = Node(label, x, y, z)
        Collection.add(self, _node)

        return _node


class Trusses(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, label, node_i, node_j, section):
        _truss = Truss(label, self.parent.nodes[node_i], self.parent.nodes[node_j], self.parent.sections[section])
        Collection.add(self, _truss)

        return _truss


class Supports(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, node, ux, uy, uz):
        _support = Support(self.parent.nodes[node], ux, uy, uz)
        Collection.add(self, _support)

        return _support


class LoadPatterns(Collection):
    def __init__(self, parent):
        Collection.__init__(self)
        self.parent = parent

    def add(self, label):
        _load_pattern = LoadPattern(label, self.parent)
        Collection.add(self, _load_pattern)

        return _load_pattern


class Structure:
    number_degrees_freedom_per_node = 3

    def __init__(self):
        self.materials = Materials(self)
        self.sections = Sections(self)

        self.nodes = Nodes(self)
        self.trusses = Trusses(self)
        self.supports = Supports(self)

        self.load_patterns = LoadPatterns(self)

    def set_degrees_freedom(self):
        for i, _node in enumerate(self.nodes):
            _node.set_degrees_freedom(np.arange(self.number_degrees_freedom_per_node * i,
                                                self.number_degrees_freedom_per_node * (i + 1)))

    def get_k(self):
        k = np.zeros(2 * (self.number_degrees_freedom_per_node * len(self.nodes),))

        for truss in self.trusses:
            degrees_freedom = np.append(truss.node_i.degrees_freedom,
                                        truss.node_j.degrees_freedom)

            for i, row in enumerate(truss.get_global_stiff_matrix()):
                for j, item in enumerate(row):
                    k[degrees_freedom[i], degrees_freedom[j]] += item

        return k

    def solve(self):
        self.set_degrees_freedom()  # Cambiar !!!

        k = self.get_k()

        for load_pattern in self.load_patterns:
            k_load_pattern = k
            f = load_pattern.get_f()

            for _support in self.supports:
                degrees_freedom = _support.node.degrees_freedom

                for i, item in enumerate(_support.restrains):
                    if item:
                        f[degrees_freedom[i], 0] = 0
                        k_load_pattern[degrees_freedom[i]] = np.zeros(np.shape(k)[0])
                        k_load_pattern[:, degrees_freedom[i]] = np.zeros(np.shape(k)[0])
                        k_load_pattern[degrees_freedom[i], degrees_freedom[i]] = 1

            u = np.linalg.solve(k_load_pattern, f)

            print("u", u, sep='\n')

            f = np.dot(k, u)

            print("f", f, sep='\n')

            for _node in self.nodes:
                degrees_freedom = _node.degrees_freedom
                _node.displacements.add(load_pattern, *u[[degree_freedom for degree_freedom in degrees_freedom], 0])

            for _support in self.supports:
                degrees_freedom = _support.node.degrees_freedom
                _support.reactions.add(load_pattern, *f[[degree_freedom for degree_freedom in degrees_freedom], 0])

    def __repr__(self):
        return self.__class__.__name__


if __name__ == '__main__':
    # structure
    structure = Structure()

    # add material
    structure.materials.add("material1", 2040e4)

    # add sections
    structure.sections.add("section1", "material1", 30e-4)
    structure.sections.add("section2", "material1", 40e-4)
    structure.sections.add("section3", "material1", 100e-4)
    structure.sections.add("section4", "material1", 150e-4)

    # add nodes
    structure.nodes.add('1', 0, 0, 0)
    structure.nodes.add('2', 8, 0, 0)
    structure.nodes.add('3', 4, 3, 0)
    structure.nodes.add('4', 4, 0, 0)

    # add trusses
    structure.trusses.add('1', '1', '3', "section3")
    structure.trusses.add('2', '1', '4', "section2")
    structure.trusses.add('3', '3', '2', "section4")
    structure.trusses.add('4', '4', '2', "section2")
    structure.trusses.add('5', '4', '3', "section1")

    # add support
    structure.supports.add('1', True, True, True)
    structure.supports.add('2', False, True, True)
    structure.supports.add('3', False, False, True)
    structure.supports.add('4', False, False, True)

    # add load pattern
    structure.load_patterns.add("point loads")

    # add point loads
    structure.load_patterns["point loads"].point_loads.add('4', 0, -20, 0)
    structure.load_patterns["point loads"].point_loads.add('3', 5 * 0.8, 5 * 0.6, 0)

    # solve the problem
    structure.solve()

    for node in structure.nodes:
        print("node {}".format(node.label))
        for displacement in node.displacements:
            print(displacement)

    print()

    for support in structure.supports:
        print("support {}".format(support.label))
        for reaction in support.reactions:
            print(reaction)

    # print(structure.materials, end='\n\n')
    # print(structure.sections, end='\n\n')
    # print(structure.nodes, end='\n\n')
    # print(structure.trusses, end='\n\n')
    # print(structure.supports, end='\n\n')
    # print(structure.load_patterns, end='\n\n')

