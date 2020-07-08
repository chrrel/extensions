"""
This module contains the database models used in this project.

This file is a copy of the file ../scanner/models.py.
"""

from peewee import Model, PrimaryKeyField, TextField, ForeignKeyField, DatabaseProxy, IntegerField
from playhouse.postgres_ext import BinaryJSONField

database_proxy = DatabaseProxy()


# Define a BaseModel which defines the database to use
class BaseModel(Model):
    class Meta:
        database = database_proxy


class Website(BaseModel):
    id = PrimaryKeyField()
    url = TextField()
    scan_time = IntegerField()


class PostMessage(BaseModel):
    id = PrimaryKeyField()
    website = ForeignKeyField(Website, backref="post_messages")
    origin = TextField()
    data = BinaryJSONField()


class SendMessage(BaseModel):
    id = PrimaryKeyField()
    website = ForeignKeyField(Website, backref="send_messages")
    extension_id = TextField()
    data = BinaryJSONField()
    call_frames = BinaryJSONField()


class PortPostMessage(BaseModel):
    id = PrimaryKeyField()
    website = ForeignKeyField(Website, backref="port_post_messages")
    extension_id = TextField()
    data = BinaryJSONField()
    call_frames = BinaryJSONField()


class Connect(BaseModel):
    id = PrimaryKeyField()
    website = ForeignKeyField(Website, backref="connect")
    extension_id = TextField()
    connect_info = BinaryJSONField()
    call_frames = BinaryJSONField()


class WarRequest(BaseModel):
    id = PrimaryKeyField()
    website = ForeignKeyField(Website, backref="war_requests")
    requested_war = TextField()
    requested_extension_id = TextField()
    request_object = BinaryJSONField()
