# toughio

![license](https://img.shields.io/badge/license-MIT-green)
[![version](https://img.shields.io/pypi/v/toughio.svg?style=flat)](https://pypi.org/project/toughio)
[![PyPi downloads](https://img.shields.io/pypi/dm/toughio.svg?style=flat)](https://pypistats.org/packages/toughio)
![black](https://img.shields.io/badge/style-black-black)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/7cb5ea7f0df9438c9c5bd74a08874aca)](https://www.codacy.com/manual/keurfonluu/toughio?utm_source=github.com&utm_medium=referral&utm_content=keurfonluu/toughio&utm_campaign=Badge_Grade)

[TOUGH](https://tough.lbl.gov/) (Transport Of Unsaturated Groundwater and Heat) is a general purpose numerical simulation software designed for fluid and heat flows of multiphase, multicomponent fluid mixtures in porous and fractured media developed at Lawrence Berkeley National Laboratory. It solves mass and energy balance equations that describe fluid and heat flow in multiphase and multicomponent systems. TOUGH handles all types of multiphase and multicomponent flow systems since the governing equations for fluid and heat flow have the same mathematical form. The nature and properties of fluid mixtures are described by thermophysical variables (e.g. density, viscosity, enthalpy) which are provided by an equation-of-state (EOS) module.

**`toughio`** is an open-source library that provides tools to facilitate pre- and post-processing for TOUGH using the latest Python standards. It aims to make setting up of a TOUGH simulation user-friendly by relying on existing well-established Python packages:

-   [**`numpy`**](https://numpy.org/): vectorized calculation of N-dimensional arrays,
-   [**`meshio`**](https://github.com/nschloe/meshio): input/output for many mesh formats,
-   [**`pyvista`**](https://github.com/pyvista/pyvista): 3D plotting and mesh analysis through a streamlined interface for the Visualization Toolkit (VTK).

Note that the results of a TOUGH simulation are sensitive to the quality of the mesh (ideally, it should satisfy the orthogonality condition). A mesh that contains too many ill-shaped cells can potentially lead to unexpected results although the simulation converged successfully. **`toughio`** does not verify the quality of the mesh which is left to the discretion of the user.

## Features

-   Create simple 2D or 3D structured meshes similarly to TOUGH's built-in _MESHMAKER_,
-   Import mesh generated by external softwares (e.g. [Abaqus](https://www.3ds.com/products-services/simulia/products/abaqus/), [FLAC3D](https://www.itascacg.com/software/flac3d), [Gmsh](http://gmsh.info/), [LaGriT](https://meshing.lanl.gov/)) and write the corresponding _MESH_ file for TOUGH **assuming [conformity](https://www.quora.com/What-is-non-conformal-mesh-in-CFD)** (and optionally write initial condition file _INCON_),
-   Easily add initial conditions, boundary conditions or other physical properties using the convenient class `toughio.Mesh`,
-   Define simulation parameters for TOUGH using the popular and more human-readable [JSON](http://json.org/) standard and write the corresponding input file for TOUGH,
-   Import outputs of a TOUGH simulation into Python,
-   Visualize results directly in Python using [**`pyvista`**](https://github.com/pyvista/pyvista) or export the results to another format supported by [**`meshio`**](https://github.com/nschloe/meshio) (e.g. VTK, Tecplot...),
-   Create animations (GIF or MP4) or export results from all time steps to a single XDMF file to be visualized in ParaView.

## Installation

The recommended way to install **`toughio`** and all its dependencies is through the Python Package Index:

```bash
pip install toughio[full] --user
```

Otherwise, clone and extract the package, then run from the package location:

```bash
pip install .[full]
```

## Usage

In Python, to read a mesh and write the corresponding TOUGH _MESH_ file (without any pre-processing), simply do

```python
import toughio

mesh = toughio.read_mesh(
    filename,
    file_format="flac3d",   # Optional, inferred from file extension otherwise
)
mesh.to_tough()             # Write MESH file
```

Parameters of a TOUGH simulation can be defined as a dictionary with specific keywords following the JSON standard, for instance

```python
parameters = {
    "title": "Sample title",
    "eos": "eco2n",
    "isothermal":, False,
    "default": {            # Default rock properties
        "density": 2600.0,
        "porosity": 0.1,
        # "permeability", "conductivity", "specific_heat"...
    },
    "rocks": {
        "shale": {          # To overwrite default rock properties
            "capillarity": {
                "id": 1,
                "parameters": [0.0, 0.0, 1.0],
            },
            # same keywords as in "default"
        },
        # other materials
    },
    "options": {
        "n_cycle": 100,
        "t_max": 3.0 * 365.25 * 24.0 * 3600.0,
        # "t_ini", "t_steps", "t_step_max", "gravity", "eps1", "eps2"...
    },
    # "extra_options", "selections", "solver", "generators"...
}
toughio.write_input("INFILE", parameters)
```

TOUGH simulation output can also be imported into Python as a list of _namedtuple_ (`time`, `labels`, `data`)

```python
output = toughio.read_output(
    filename,
    file_format="tough",    # Optional, "tough" or "tecplot"
)
```

**`toughio`** is mainly intended to be used as a Python scripting library for TOUGH. Nevertheless, several utility command line scripts are available for users who are not familiar with Python. From a console or terminal, the user can execute the following scripts:

-   `toughio-export`: export TOUGH simulation results to a file for visualization (VTK, VTU or Tecplot),
-   `toughio-extract`: extract results from TOUGH main output file and reformat as a TOUGH3 element output file (mostly useful for TOUGH2 output _before_ calling `toughio-export`),
-   `toughio-merge`: merge input file, MESH and/or INCON into a single file (for storage or sharing).
