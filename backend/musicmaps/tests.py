from django.test import TestCase
from .documents import Post

import time
from elasticsearch.exceptions import ConflictError


class PostDocumentsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        post = Post(
            open_range=1,
            author_id=1,
            comments_on=1,
            content="아 코딩하기 시러어어ㅓㅓㅇ",
            coordinates={"lat": 37.535397, "lon": 127.054437},
            street_address="서울특별시 성동구 둘레15길",
            building_number=7
        )
        post.save()
        time.sleep(1)

    def test_coordinates(self):
        s = Post.search(index='musicmaps')
        response = s.execute()
        self.assertEquals(response[0].coordinates, {"lat": 37.535397, "lon": 127.054437})

    def test_geo_query(self):
        coordinates = {"lat": 37.535397, "lon": 127.054437}
        s = Post.search(index='musicmaps').filter({
            'geo_distance': {
                "distance": "1km",
                "coordinates":
                    {"lat": coordinates.get("lat"),
                     "lon": coordinates.get("lon")}
            }
        })
        response = s.execute()
        self.assertEquals(response[0].coordinates, {"lat": 37.535397, "lon": 127.054437})

    def test_add_comment(self):
        s = Post.search(index='musicmaps')
        response = s.execute()
        post_id = response[0].meta.id
        post = Post.get(id=post_id)
        post.add_comment(author_id=1, content="이것이 댓글")
        post.save()
        self.assertEquals(post.comments[0].content, "이것이 댓글")

    def test_update_comment(self):
        s = Post.search(index='musicmaps')
        response = s.execute()
        post_id = response[0].meta.id
        post = Post.get(id=post_id)
        post.update_comment(author_id=1, content="이것이 댓글", index=1)
        post.update()
        self.assertEquals(post.comments[0].content, "이것이 댓글")

    def test_delete_post(self):
        def delete(search):
            try:
                return search.delete()
            except ConflictError:
                time.sleep(1)
                return delete(search)
        s = Post.search(index='musicmaps').query('match', author_id=1)
        response = delete(s)
        self.assertGreater(response.deleted, 0)

