import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Callable, Any
from abc import ABC, abstractmethod
import aio_pika
import os
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import BackgroundTasks
from core.config.settings import get_settings
from core.repositories.document_repo import DocumentRepository, ConversionTaskRepository
from core.services.document_conversion_service import DocumentConversionService

settings = get_settings()


class MessageBrokerBase(ABC):
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def publish_task(self, document_id: int, task_id: str) -> None:
        pass
    
    @abstractmethod
    async def consume_tasks(self, callback: Callable, queue_name: str = "document_conversion") -> None:
        pass


class RabbitMQBroker(MessageBrokerBase):
    
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.rabbitmq_url = settings.RABBITMQ_URL or "amqp://guest:guest@rabbitmq:5672/"
    
    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            await self.channel.set_qos(prefetch_count=10)
            
            print(f"[RabbitMQ] Подключено к {self.rabbitmq_url}")
        except Exception as e:
            print(f"[RabbitMQ] Ошибка подключения: {e}")
            raise
    
    async def disconnect(self) -> None:
        if self.connection:
            await self.connection.close()
            print("[RabbitMQ] Отключено")
    
    async def publish_task(self, document_id: int, task_id: str) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ не подключен")
        
        queue_name = "document_conversion"
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
        )
        
        message_body = json.dumps({
            "document_id": document_id,
            "task_id": task_id,
            "created_at": datetime.utcnow().isoformat(),
        }).encode()
        
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        await self.channel.default_exchange.publish(message, routing_key=queue_name)
        print(f"[RabbitMQ] Задача опубликована: document_id={document_id}, task_id={task_id}")
    
    async def consume_tasks(
        self,
        callback: Callable,
        queue_name: str = "document_conversion",
    ) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ не подключен")

        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        document_id = body["document_id"]
                        task_id = body["task_id"]
                        
                        print(f"[RabbitMQ] Получена задача: document_id={document_id}")
                        
                        await callback(document_id, task_id)
                        
                    except Exception as e:
                        print(f"[RabbitMQ] Ошибка обработки задачи: {e}")
                    

class KafkaBroker(MessageBrokerBase):
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.kafka_bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS or "kafka:9092"
        self.topic = "document_conversion"
    
    async def connect(self) -> None:
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self.producer.start()
            
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id="document_conversion_group",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            await self.consumer.start()
            
            print(f"[Kafka] Подключено к {self.kafka_bootstrap_servers}")
        except Exception as e:
            print(f"[Kafka] Ошибка подключения: {e}")
            raise
    
    async def disconnect(self) -> None:
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
        print("[Kafka] Отключено")
    
    async def publish_task(self, document_id: int, task_id: str) -> None:
        if not self.producer:
            raise RuntimeError("Kafka producer не подключен")
        
        message = {
            "document_id": document_id,
            "task_id": task_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await self.producer.send_and_wait(self.topic, value=message)
        print(f"[Kafka] Задача опубликована: document_id={document_id}, task_id={task_id}")
    
    async def consume_tasks(
        self,
        callback: Callable,
        queue_name: str = "document_conversion",
    ) -> None:
        if not self.consumer:
            raise RuntimeError("Kafka consumer не подключен")
        
        try:
            async for msg in self.consumer:
                try:
                    body = msg.value
                    document_id = body["document_id"]
                    task_id = body["task_id"]
                    
                    print(f"[Kafka] Получена задача: document_id={document_id}")
                    await callback(document_id, task_id)

                    self.consumer.commit()
                    
                except Exception as e:
                    print(f"[Kafka] Ошибка обработки задачи: {e}")
        except asyncio.CancelledError:
            print("[Kafka] Потребление остановлено")


class AsyncConversionService:
    
    def __init__(self, session):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.task_repo = ConversionTaskRepository(session)
        self.conversion_service = DocumentConversionService(session)
        self.broker: Optional[MessageBrokerBase] = None
        self._init_broker()
        
        self._consumer_task: Optional[asyncio.Task] = None
    
    def _init_broker(self) -> None:
        broker_type = settings.MESSAGE_BROKER or "background"
        
        if broker_type == "rabbitmq":
            self.broker = RabbitMQBroker()
        elif broker_type == "kafka":
            self.broker = KafkaBroker()
        else:
            self.broker = None
            print("[AsyncConversion] Используем BackgroundTasks (без брокера)")
    
    async def start(self) -> None:
        if self.broker:
            await self.broker.connect()
            self._consumer_task = asyncio.create_task(
                self.broker.consume_tasks(self._process_task)
            )
            print("[AsyncConversion] Потребитель задач запущен")
    
    async def stop(self) -> None:
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        if self.broker:
            await self.broker.disconnect()
    
    async def submit_conversion_task(
        self,
        document_id: int,
        background_tasks: BackgroundTasks,
    ) -> str:
        task_id = str(uuid.uuid4())
        await self.task_repo.create_task(document_id, task_id)
        
        if self.broker:
            await self.broker.publish_task(document_id, task_id)
        else:
            background_tasks.add_task(self._process_task, document_id, task_id)
        
        return task_id
    
    async def _process_task(self, document_id: int, task_id: str) -> None:

        print(f"[AsyncConversion] Начало обработки: document_id={document_id}")
        
        task = await self.task_repo.get_by_task_id(task_id)
        if not task:
            print(f"[AsyncConversion] Задача не найдена: {task_id}")
            return
        
        await self.task_repo.update_status(task.id, "processing")
        
        try:
            success, message, converted_path = await self.conversion_service.convert_document(
                document_id=document_id,
            )
            
            if success:
                await self.task_repo.update_status(task.id, "completed")
                print(f"[AsyncConversion] Задача завершена: {document_id}")
            else:
                await self.task_repo.update_status(task.id, "failed", message)
                print(f"[AsyncConversion] Задача не удалась: {document_id} - {message}")
                
        except Exception as e:
            await self.task_repo.update_status(task.id, "failed", str(e))
            print(f"[AsyncConversion] Ошибка задачи: {document_id} - {e}")
    
    async def get_task_status(self, document_id: int) -> dict:
        task = await self.task_repo.get_by_document_id(document_id)
        
        if not task:
            return {
                "status": "not_found",
                "message": "Задача не найдена",
            }
        
        document = await self.doc_repo.get_by_id(document_id)
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "document_id": document_id,
            "conversion_status": document.conversion_status if document else None,
            "converted_path": document.converted_path if document else None,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
    
    async def get_pending_tasks_count(self) -> int:
        tasks = await self.task_repo.get_pending_tasks(limit=1000)
        return len(tasks)


class CacheService:

    CACHE_TTL_HOURS = 24
    
    def __init__(self, session):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.conversion_service = DocumentConversionService(session)
    
    async def get_cached_pdf_path(self, document_id: int) -> Optional[str]:

        document = await self.doc_repo.get_by_id(document_id)
        
        if not document:
            return None
        if (
            document.converted_path
            and document.conversion_status == "completed"
            and document.cache_expires_at
            and document.cache_expires_at > datetime.utcnow()
        ):
            if os.path.exists(document.converted_path):
                return document.converted_path
        
        return None
    
    async def refresh_cache(self, document_id: int) -> bool:

        document = await self.doc_repo.get_by_id(document_id)
        
        if not document or not document.converted_path:
            return False
        
        from datetime import timedelta
        document.cache_expires_at = datetime.utcnow() + timedelta(hours=self.CACHE_TTL_HOURS)
        await self.session.flush()
        
        return True
    
    async def cleanup_expired(self) -> int:
        return await self.conversion_service.cleanup_expired_cache()
