import pytest
from fastapi.testclient import TestClient

from paper_agent.app import create_app
from paper_agent.config import Settings
from paper_agent.store import Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, provider="evidence"))
    with TestClient(app) as value:
        yield value
