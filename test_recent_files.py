import tempfile
from pathlib import Path

from engine.storage import RecentFilesManager


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    storage = root / "recent.json"
    first = root / "first.ksproj"
    second = root / "second.ksproj"
    third = root / "third.ksproj"
    missing = root / "missing.ksproj"

    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")
    third.write_text("{}", encoding="utf-8")

    manager = RecentFilesManager(storage, max_count=2)
    manager.add(first, timestamp="2026-01-01T00:00:00+00:00")
    manager.add(second, pinned=True, timestamp="2026-01-02T00:00:00+00:00")
    manager.add(third, timestamp="2026-01-03T00:00:00+00:00")

    paths = manager.paths()
    assert str(second.resolve()) == paths[0]
    assert str(third.resolve()) in paths
    assert str(first.resolve()) not in paths

    manager.add(missing, timestamp="2026-01-04T00:00:00+00:00")
    manager.remove_missing()
    assert str(missing.resolve()) not in manager.paths()

    manager.unpin(second)
    assert not manager._entries[str(second.resolve())].pinned

    reloaded = RecentFilesManager(storage, max_count=2)
    assert reloaded.count == manager.count

print("recent-files-ok")
