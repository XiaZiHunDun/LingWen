"""Default CVG storage singleton attaches reference graph for cascade BFS."""
from __future__ import annotations

from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph


class TestDefaultStorageGraph:
    def test_default_storage_attaches_reference_graph(self, monkeypatch, tmp_path):
        from dashboard import app as app_module

        monkeypatch.setattr(app_module, "_default_storage_instance", None)
        monkeypatch.setattr(app_module, "_DEFAULT_CVG_DB_PATH", tmp_path / "default_storage_graph.db")

        storage = app_module._default_storage()
        assert storage._graph is not None
        assert isinstance(storage._graph, CrossVolumeReferenceGraph)

        # Idempotent: second call returns same instance with graph intact.
        storage_again = app_module._default_storage()
        assert storage_again is storage
        assert storage_again._graph is storage._graph
