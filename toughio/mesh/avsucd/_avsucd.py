from __future__ import division, unicode_literals, with_statement

import logging

import numpy

from ...__about__ import __version__ as version
from .._common import meshio_data
from .._mesh import Cells, Mesh

__all__ = [
    "read",
    "write",
]


meshio_to_avsucd_type = {
    "vertex": "pt",
    "line": "line",
    "triangle": "tri",
    "quad": "quad",
    "tetra": "tet",
    "pyramid": "pyr",
    "wedge": "prism",
    "hexahedron": "hex",
}
avsucd_to_meshio_type = {v: k for k, v in meshio_to_avsucd_type.items()}


meshio_to_avsucd_order = {
    "vertex": [0],
    "line": [0, 1],
    "triangle": [0, 1, 2],
    "quad": [0, 1, 2, 3],
    "tetra": [0, 1, 3, 2],
    "pyramid": [4, 0, 1, 2, 3],
    "wedge": [3, 4, 5, 0, 1, 2],
    "hexahedron": [4, 5, 6, 7, 0, 1, 2, 3],
}


avsucd_to_meshio_order = {
    k: (v if k != "pyramid" else [1, 2, 3, 4, 0])
    for k, v in meshio_to_avsucd_order.items()
}


def read(filename):
    """Read AVS-UCD ASCII file."""
    with open(filename, "r") as f:
        out = read_buffer(f)
    return out


def read_buffer(f):
    # Skip comments and unpack first line
    num_nodes, num_cells, num_node_data, num_cell_data, _ = numpy.genfromtxt(
        f, max_rows=1, dtype=int, comments="#"
    )

    # Read nodes
    point_ids, points = _read_nodes(f, num_nodes)

    # Read cells
    cell_ids, cells, cell_data = _read_cells(f, num_cells, point_ids)

    # Read node data
    if num_node_data:
        point_data = _read_data(f, num_nodes, point_ids)
    else:
        point_data = {}

    # Read cell data
    if num_cell_data:
        cdata = _read_data(f, num_cells, cell_ids)
        sections = numpy.cumsum([len(c[1]) for c in cells[:-1]])
        for k, v in cdata.items():
            cell_data[k] = numpy.split(v, sections)

    return Mesh(points, cells, point_data=point_data, cell_data=cell_data)


def _read_nodes(f, num_nodes):
    data = numpy.genfromtxt(f, max_rows=num_nodes)
    points_ids = {int(pid): i for i, pid in enumerate(data[:, 0])}
    return points_ids, data[:, 1:]


def _read_cells(f, num_cells, point_ids):
    cells = []
    cell_ids = {}
    cell_data = {"avsucd:material": []}
    count = 0
    for _ in range(num_cells):
        line = f.readline().strip().split()
        cell_id = int(line[0])
        cell_mat = int(line[1])
        cell_type = avsucd_to_meshio_type[line[2]]
        corner = [point_ids[int(pid)] for pid in line[3:]]

        if len(cells) > 0 and cells[-1].type == cell_type:
            cells[-1].data.append(corner)
            cell_data["avsucd:material"][-1].append(cell_mat)
        else:
            cells.append(Cells(cell_type, [corner]))
            cell_data["avsucd:material"].append([cell_mat])

        cell_ids[cell_id] = count
        count += 1

    # Convert to numpy arrays
    for k, c in enumerate(cells):
        cells[k] = Cells(c.type, numpy.array(c.data)[:, avsucd_to_meshio_order[c.type]])
        cell_data["avsucd:material"][k] = numpy.array(cell_data["avsucd:material"][k])
    return cell_ids, cells, cell_data


def _read_data(f, num_entities, entity_ids):
    line = f.readline().strip().split()
    data_size = [int(i) for i in line[1:]]

    labels = {}
    data = {}
    for i, dsize in enumerate(data_size):
        line = f.readline().strip().split(",")
        labels[i] = line[0].strip().replace(" ", "_")
        data[labels[i]] = (
            numpy.empty(num_entities)
            if dsize == 1
            else numpy.empty((num_entities, dsize))
        )

    for _ in range(num_entities):
        line = f.readline().strip().split()
        eid = entity_ids[int(line[0])]
        j = 0
        for i, dsize in enumerate(data_size):
            if dsize == 1:
                data[labels[i]][eid] = float(line[j + 1])
            else:
                data[labels[i]][eid] = [
                    float(val) for val in line[j + 1 : j + 1 + dsize]
                ]
            j += dsize
    return data


def write(filename, mesh):
    """Write AVS-UCD ASCII file."""
    if mesh.points.shape[1] == 2:
        logging.warning(
            "AVS-UCD requires 3D points, but 2D points given. "
            "Appending 0 third component."
        )
        mesh.points = numpy.column_stack(
            [mesh.points[:, 0], mesh.points[:, 1], numpy.zeros(mesh.points.shape[0])]
        )

    with open(filename, "w") as f:
        # Write meshio version
        f.write("# Written by toughio v{}\n".format(version))

        # Write first line
        num_nodes = len(mesh.points)
        num_cells = sum(len(c.data) for c in mesh.cells)
        num_node_data = [
            1 if v.ndim == 1 else v.shape[1] for v in mesh.point_data.values()
        ]
        num_cell_data = [
            1 if vv.ndim == 1 else vv.shape[1]
            for k, v in mesh.cell_data.items()
            for vv in v
            if k not in meshio_data
        ]
        num_node_data_sum = sum(num_node_data)
        num_cell_data_sum = sum(num_cell_data)
        f.write(
            "{} {} {} {} 0\n".format(
                num_nodes, num_cells, num_node_data_sum, num_cell_data_sum
            )
        )

        # Write nodes
        _write_nodes(f, mesh.points)

        # Write cells
        _write_cells(f, mesh.cells, mesh.cell_data, num_cells)

        # Write node data
        if num_node_data_sum:
            labels = mesh.point_data.keys()
            data_array = numpy.column_stack([v for v in mesh.point_data.values()])
            _write_data(
                f, labels, data_array, num_nodes, num_node_data, num_node_data_sum
            )

        # Write cell data
        if num_cell_data_sum:
            labels = [k for k in mesh.cell_data.keys() if k not in meshio_data]
            data_array = numpy.column_stack(
                [
                    numpy.concatenate(v)
                    for k, v in mesh.cell_data.items()
                    if k not in meshio_data
                ]
            )
            _write_data(
                f, labels, data_array, num_cells, num_cell_data, num_cell_data_sum
            )


def _write_nodes(f, points):
    for i, (x, y, z) in enumerate(points):
        f.write("{} {} {} {}\n".format(i + 1, x, y, z))


def _write_cells(f, cells, cell_data, num_cells):
    # Interoperability with other formats
    mat_data = None
    for k in cell_data.keys():
        if k in meshio_data:
            mat_data = k
            break

    # Material array
    if mat_data:
        material = numpy.concatenate(cell_data[mat_data])
    else:
        material = numpy.zeros(num_cells, dtype=int)

    # Loop over cells
    i = 0
    for k, v in cells:
        for cell in v[:, meshio_to_avsucd_order[k]]:
            cell_str = " ".join(str(c + 1) for c in cell)
            f.write(
                "{} {} {} {}\n".format(
                    i + 1, int(material[i]), meshio_to_avsucd_type[k], cell_str
                )
            )
            i += 1


def _write_data(f, labels, data_array, num_entities, num_data, num_data_sum):
    num_data_str = " ".join(str(i) for i in num_data)
    f.write("{} {}\n".format(len(num_data), num_data_str))

    for label in labels:
        f.write("{}, real\n".format(label))

    data_array = numpy.column_stack((numpy.arange(1, num_entities + 1), data_array))
    numpy.savetxt(f, data_array, delimiter=" ", fmt=["%d"] + ["%.14e"] * num_data_sum)
