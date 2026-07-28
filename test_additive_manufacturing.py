from pathlib import Path
from tempfile import TemporaryDirectory

from engine.storage.project import ProjectSerializer
from engine.workspace import Workspace


def test_additive_manufacturing_slicing_print_files_and_persistence():
    workspace = Workspace("Additive Manufacturing Project")
    machine_workspace = workspace.machine_workspace.initialize()
    engine = workspace.manufacturing_engine.initialize()

    fdm_machine = machine_workspace.register_machine(
        "KS FDM Pro",
        "FDM Printer",
        manufacturer="Kinematics Studio",
        model="FDM Pro",
        firmware="Klipper",
        work_envelope={"x": 220, "y": 220, "z": 250},
        supported_materials=["PLA"],
        supported_tool_systems=["Extruder"],
        supported_file_formats=["GCODE", "3MF"],
    )
    sla_machine = machine_workspace.register_machine(
        "KS SLA Pro",
        "SLA Printer",
        manufacturer="Kinematics Studio",
        model="SLA Pro",
        firmware="Photon",
        work_envelope={"x": 130, "y": 80, "z": 160},
        supported_materials=["Resin"],
        supported_tool_systems=["Resin Vat"],
        supported_file_formats=["CTB", "PHOTON"],
    )
    tools = machine_workspace.create_tool_library("Additive Production Tools")
    nozzle = machine_workspace.register_tool(
        tools,
        "0.4mm Hardened Nozzle",
        "Extruder",
        diameter=0.4,
        length=12.0,
        material="Hardened Steel",
        operating_limits={"max_temperature": 300, "max_flow": 18},
    )
    vat = machine_workspace.register_tool(
        tools,
        "Standard Resin Vat",
        "Resin Vat",
        diameter=0.0,
        length=0.0,
        material="FEP",
        operating_limits={"max_layers": 2000},
    )
    pla = machine_workspace.register_material(
        "PLA",
        "Plastic",
        density=1240,
        color="#4dd0e1",
        manufacturing_notes="Production FDM filament.",
        compatible_machines=[fdm_machine],
        default_process_metadata={
            "temperature": {"nozzle": 205, "bed": 60},
            "cooling": {"fan_speed": 100},
            "drying": {"temperature": 45, "hours": 4},
            "storage": {"humidity_percent": 20},
        },
    )
    resin = machine_workspace.register_material(
        "Standard Resin",
        "Resin",
        density=1100,
        color="#f6d365",
        manufacturing_notes="Production SLA resin.",
        compatible_machines=[sla_machine],
        default_process_metadata={
            "exposure": {"normal": 2.2, "bottom": 24.0},
            "lift": {"distance": 6.0, "speed": 60.0},
            "shrinkage": {"xy": 0.01, "z": 0.015},
            "storage": {"temperature": 22},
        },
    )
    fdm_profile = machine_workspace.create_profile(fdm_machine, "FDM PLA Production", tool_library=tools)
    sla_profile = machine_workspace.create_profile(sla_machine, "SLA Resin Production", tool_library=tools)
    machine_workspace.activate_profile(fdm_profile)

    fdm_job = engine.create_additive_job(
        "FDM Gear Cover",
        "FDM",
        machine_profile=fdm_profile,
        material=pla,
        model_dimensions={"x": 40, "y": 30, "z": 12},
        quantity=2,
    )
    fdm_params = engine.configure_print_parameters(
        fdm_job,
        technology="FDM",
        layer_height=0.2,
        nozzle_diameter=0.4,
        extrusion_width=0.45,
        line_count=3,
        wall_thickness=1.2,
        top_thickness=0.8,
        bottom_thickness=0.8,
        infill_percentage=25,
        infill_pattern="Grid",
        print_speed=60,
        travel_speed=150,
        acceleration=1200,
        jerk=8,
        temperature={"nozzle": 205, "bed": 60},
        cooling={"fan_speed": 100},
        retraction={"enabled": True, "distance": 1.2, "speed": 35},
        z_hop={"enabled": True, "height": 0.2},
        adaptive_layers=True,
        material_metadata={"drying": "4h at 45C"},
    )
    fdm_layout = engine.plan_build_plate(fdm_job, brim=True, skirt=True, raft=False, prime_tower={"enabled": False})
    fdm_support = engine.generate_supports(
        fdm_job,
        support_type="Tree",
        density=18,
        blockers=["logo"],
        enforcers=["overhang"],
    )
    fdm_slice = engine.slice_fdm(fdm_job, fdm_params, fdm_support)
    generic = engine.generate_print_file(fdm_job, "Generic G-code")
    klipper = engine.generate_print_file(fdm_job, "Klipper G-code")
    marlin = engine.generate_print_file(fdm_job, "Marlin G-code")
    bambu = engine.generate_print_file(fdm_job, "Bambu-compatible metadata foundation")

    assert fdm_layout.valid is True
    assert len(fdm_slice.layers) == 60
    assert fdm_slice.valid is True
    assert fdm_slice.layers[0].perimeters
    assert fdm_slice.layers[0].walls
    assert fdm_slice.layers[4].infill
    assert any(layer.supports for layer in fdm_slice.layers)
    assert fdm_slice.material_usage["filament_length"] > 0
    assert "G21" in generic.content and "M30" in generic.content
    assert "SET_VELOCITY_LIMIT" in klipper.content
    assert "G21" in marlin.content
    assert "BAMBU_METADATA_BEGIN" in bambu.content
    assert nozzle.metadata.properties["operating_limits"]["max_flow"] == 18

    sla_job = engine.create_additive_job(
        "SLA Dental Guide",
        "SLA",
        machine_profile=sla_profile,
        material=resin,
        model_dimensions={"x": 30, "y": 20, "z": 8},
        quantity=1,
    )
    sla_params = engine.configure_print_parameters(
        sla_job,
        technology="SLA",
        layer_height=0.05,
        resin={"viscosity": "standard"},
        hollowing={"enabled": True, "wall_thickness": 2.0},
        drain_holes=[{"x": 8, "y": 8, "diameter": 2.0}],
        orientation={"x": 20, "y": 0, "z": 0},
        exposure={"normal": 2.2, "bottom": 24.0},
        lift={"distance": 6.0, "speed": 60.0, "time": 5.0},
        resin_profile={"name": "Standard Resin"},
    )
    sla_layout = engine.plan_build_plate(sla_job)
    sla_support = engine.generate_supports(sla_job, support_type="Organic", density=25)
    sla_slice = engine.slice_sla(sla_job, sla_params, sla_support)
    ctb = engine.generate_print_file(sla_job, "CTB foundation")
    photon = engine.generate_print_file(sla_job, "Photon foundation")

    assert sla_layout.valid is True
    assert len(sla_slice.layers) == 160
    assert sla_slice.valid is True
    assert sla_slice.layers[0].exposure["normal"] == 2.2
    assert any(layer.supports for layer in sla_slice.layers)
    assert sla_slice.material_usage["resin_volume"] > 0
    assert "BEGIN_LAYERS" in ctb.content
    assert "BEGIN_LAYERS" in photon.content
    assert vat.metadata.properties["operating_limits"]["max_layers"] == 2000

    validation = engine.validate()
    diagnostics = engine.diagnostics()

    assert validation.valid is True
    assert diagnostics.execution_plan_statistics["additive_slices"] == 2
    assert diagnostics.execution_plan_statistics["additive_print_files"] == 6
    assert diagnostics.execution_plan_statistics["additive_layers"] == 220
    assert diagnostics.execution_plan_statistics["estimated_filament_length"] > 0
    assert diagnostics.execution_plan_statistics["estimated_resin_volume"] > 0
    assert len(workspace.product_manager.slice_jobs) == 2
    assert len(workspace.product_manager.slice_profiles) == 2
    assert len(workspace.product_manager.slice_operations) == 2

    assert list(workspace.scene3d.entities()) == []
    assert getattr(workspace.product_manager, "bodies", []) == []
    assert getattr(workspace.product_manager, "features", []) == []
    assert workspace.command_manager.undo_stack == []
    assert workspace.command_manager.redo_stack == []

    with TemporaryDirectory() as directory:
        path = Path(directory) / "additive_manufacturing.ksproj"
        ProjectSerializer().save(workspace, path)
        restored = ProjectSerializer().load(path)

    restored_machine_workspace = restored.machine_workspace
    restored_machine_workspace.load_from_settings()
    restored_engine = restored.manufacturing_engine
    restored_engine.load_from_settings()

    assert len(restored_engine.additive_parameters) == 2
    assert len(restored_engine.build_plate_layouts) == 2
    assert len(restored_engine.additive_slices) == 2
    assert len(restored_engine.additive_print_files) == 6
    assert len(restored.product_manager.slice_jobs) == 2
    assert len(restored.product_manager.slice_profiles) == 2
    assert len(restored.product_manager.slice_operations) == 2
    assert restored_engine.validate().valid is True
    assert list(restored.scene3d.entities()) == []
    assert getattr(restored.product_manager, "bodies", []) == []
    assert getattr(restored.product_manager, "features", []) == []
    assert restored.command_manager.undo_stack == []
    assert restored.command_manager.redo_stack == []


if __name__ == "__main__":
    test_additive_manufacturing_slicing_print_files_and_persistence()
    print("additive-manufacturing-ok")
