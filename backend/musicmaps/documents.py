from datetime import datetime
from elasticsearch_dsl import Document, Date, Nested, Boolean, InnerDoc, Text, Integer, GeoPoint


class Comment(InnerDoc):
    author_id = Integer(required=True)
    content = Text(required=True)
    created_at = Date()

    def age(self):
        return datetime.now() - self.created_at


class Music(InnerDoc):
    artists = Text()
    name = Text()
    yt_song_id = Text()


class Post(Document):
    images = Text(multi=True)
    created_at = Date()
    last_updated_at = Date()
    open_range = Integer(required=True)
    author_id = Integer(required=True)
    comments_on = Boolean(required=True)
    comments = Nested(Comment)
    playlist = Nested(Music)
    content = Text()
    coordinates = GeoPoint(required=True)
    street_address = Text(required=True)
    building_number = Integer(required=True)

    class Index:
        name = 'musicmaps'

    def add_comment(self, author_id, content):
        self.comments.append(
            Comment(author_id=author_id, content=content, created_at=datetime.now())
        )

    def save(self, **kwargs):
        self.created_at= datetime.now()
        self.last_updated_at = datetime.now()
        return super().save(**kwargs)
