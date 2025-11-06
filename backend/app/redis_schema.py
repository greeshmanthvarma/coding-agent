import redis
from redis.commands.json.path import Path
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import redis.exceptions
import os


def create_messages_index(redis_client: redis.Redis):
    """
    Create Redis search index for messages if it doesn't exist.
    Call this on application startup.
    """
    index_name = "idx:messages"
    
    try:
        
        redis_client.ft(index_name).info()
        return {"message": f"Index {index_name} already exists"}
    
    except redis.exceptions.ResponseError:
        pass
    
    schema = (
        TextField("$.message", as_name="message"), 
        TagField("$.sender", as_name="sender"), 
        TagField("$.session_id", as_name="session_id"),
        NumericField("$.sequence", as_name="sequence")
    )
    
    try:
        redis_client.ft(index_name).create_index(
            schema,
            definition=IndexDefinition(
                prefix=["message:"], index_type=IndexType.JSON
            )
        )
        return {"message": f"Index {index_name} created successfully"}
    except Exception as e:
        return {"message": f"Error creating index {index_name}: {e}", "error": str(e)}