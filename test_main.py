import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from models import InsertRequest, Node, Relationship
from dotenv import load_dotenv
import os

# Загрузка конфигурации
load_dotenv()
auth_token=os.getenv('AUTH_TOKEN')

# Фикстура для клиента FastAPI
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

# Мокаем Neo4jStorage для тестов
@pytest.fixture(autouse=True)
def mock_neo4j_storage(monkeypatch):
    mock_storage = MagicMock()
    # Мокаем методы Neo4jStorage с предсказуемыми значениями
    mock_storage.get_all_nodes.return_value = [
        {"id": 0, "label": "User"},
        {"id": 1, "label": "Group"},
        {"id": 2, "label": "User"}
    ]
    mock_storage.get_node_with_relationships.return_value = {
        "node": {"id": 0, "label": "User"},
        "relationships": [
            {"relationship_type": "FOLLOWS", "end_node_id": 2}
        ]
    }
    mock_storage.add_node_and_relationships.return_value = None
    mock_storage.delete_node_and_relationships.return_value = None
    app.state.neo4j_handler = mock_storage
    return mock_storage

# Тест для получения всех узлов
def test_find_all_nodes(client):
    response = client.get("/nodes")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 0, "label": "User"},
        {"id": 1, "label": "Group"},
        {"id": 2, "label": "User"}
    ]

# Тест для получения узла и его связей
def test_find_node_with_relationships(client):
    node_id = 0
    response = client.get(f"/node/{node_id}")
    assert response.status_code == 200
    assert response.json() == {
        "node": {"id": node_id, "label": "User"},
        "relationships": [
            {"relationship_type": "FOLLOWS", "end_node_id": 2}
        ]
    }

# Тест для добавления узла и его связей
def test_insert_node_and_relationships(client):
    node = Node(id=3, label="User", name="Илья", screen_name="n1ki", sex=2, city="Тюмень")
    relationships = [Relationship(type="FOLLOWS", end_node_id=2)]
    node_with_rels = InsertRequest(node=node, relationships=relationships)
    
    response = client.post("/node", json=node_with_rels.model_dump(), headers={"token": f"{auth_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Новый узел и его связи успешно добавлены"}

# Тест для удаления узла и его связей
def test_remove_node_and_relationships(client):
    node_id = 3
    response = client.delete(f"/node/{node_id}", headers={"token": f"{auth_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Узел и все его связи успешно удалены"}

# Тест для проверки недействительного токена
def test_verify_token_invalid(client):
    response = client.post("/node", headers={"token": "invalid_token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}