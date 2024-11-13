from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from storage import Neo4jStorage
from auth import verify_token
from models import InsertRequest
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяет, создан ли обработчик Neo4j, чтобы избежать дублирования
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "neo4j_handler"):
        neo4j_handler = Neo4jStorage(
            os.getenv("NEO4J_URI"),
            os.getenv("NEO4J_USER"),
            os.getenv("NEO4J_PASSWORD")
        )
        app.state.neo4j_handler = neo4j_handler
    yield
    # Закрывает соединение с Neo4j при завершении работы приложения
    if hasattr(app.state, "neo4j_handler"):
        app.state.neo4j_handler.close()

app = FastAPI(lifespan=lifespan)

# Возвращает все узлы с их идентификаторами и метками
@app.get("/nodes")
def find_all_nodes():
    return app.state.neo4j_handler.get_all_nodes()

# Возвращает узел с указанным идентификатором и его связи с атрибутами
@app.get("/node/{node_id}")
def find_node_with_relationships(node_id: int):
    return app.state.neo4j_handler.get_node_with_relationships(node_id)

# Добавляет новый узел и его связи в базу данных
@app.post("/node", dependencies=[Depends(verify_token)])
def insert_node_and_relationships(node_with_rels: InsertRequest):
    app.state.neo4j_handler.add_node_and_relationships(node_with_rels)
    return {"message": "Новый узел и его связи успешно добавлены"}

# Удаляет указанный узел и все его связи из базы данных
@app.delete("/node/{node_id}", dependencies=[Depends(verify_token)])
def remove_node_and_relationships(node_id: int):
    app.state.neo4j_handler.delete_node_and_relationships(node_id)
    return {"message": "Узел и все его связи успешно удалены"}