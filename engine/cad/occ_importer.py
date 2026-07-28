from pathlib import Path

from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone


class OCCImporter:
    """Imports CAD files into OpenCascade TopoDS_Shape objects."""

    SUPPORTED = {
        ".step",
        ".stp",
        ".brep",
    }

    # -----------------------------------------------------

    def import_file(self, filename):

        filename = Path(filename)

        suffix = filename.suffix.lower()

        if suffix in (".step", ".stp"):
            return self.import_step(filename)

        if suffix == ".brep":
            return self.import_brep(filename)

        raise ValueError(f"Unsupported CAD format: {suffix}")

    # -----------------------------------------------------

    def import_step(self, filename):

        reader = STEPControl_Reader()

        status = reader.ReadFile(str(filename))

        if status != IFSelect_RetDone:
            raise RuntimeError(f"Unable to read STEP file:\n{filename}")

        reader.TransferRoots()

        return reader.OneShape()

    # -----------------------------------------------------

    def import_brep(self, filename):

        builder = BRep_Builder()

        shape = TopoDS_Shape()

        ok = BRepTools.Read_s(
            shape,
            str(filename),
            builder,
        )

        if not ok:
            raise RuntimeError(f"Unable to read BREP file:\n{filename}")

        return shape

    # -----------------------------------------------------

    def import_into_manager(
        self,
        filename,
        occ_manager,
    ):

        shape = self.import_file(filename)

        occ_manager.add(shape)

        return shape