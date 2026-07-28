from pathlib import Path

from OCP.BRepTools import BRepTools
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone


class OCCExporter:
    """Exports OpenCascade TopoDS_Shapes."""

    SUPPORTED = {
        ".step",
        ".stp",
        ".brep",
    }

    # -----------------------------------------------------

    def export_file(
        self,
        shape,
        filename,
    ):

        filename = Path(filename)

        suffix = filename.suffix.lower()

        if suffix in (".step", ".stp"):
            return self.export_step(shape, filename)

        if suffix == ".brep":
            return self.export_brep(shape, filename)

        raise ValueError(f"Unsupported export format: {suffix}")

    # -----------------------------------------------------

    def export_step(
        self,
        shape,
        filename,
    ):

        writer = STEPControl_Writer()

        writer.Transfer(
            shape,
            STEPControl_AsIs,
        )

        status = writer.Write(str(filename))

        if status != IFSelect_RetDone:
            raise RuntimeError(
                f"Failed to export STEP:\n{filename}"
            )

        return filename

    # -----------------------------------------------------

    def export_brep(
        self,
        shape,
        filename,
    ):

        ok = BRepTools.Write_s(
            shape,
            str(filename),
        )

        if not ok:
            raise RuntimeError(
                f"Failed to export BREP:\n{filename}"
            )

        return filename

    # -----------------------------------------------------

    def export_manager(
        self,
        occ_manager,
        filename,
    ):

        if not occ_manager.shapes:
            raise RuntimeError("No OCC shapes available.")

        return self.export_file(
            occ_manager.shapes[-1],
            filename,
        )