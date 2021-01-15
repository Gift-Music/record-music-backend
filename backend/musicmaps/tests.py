from django.test import TestCase
from .documents import Post, Location, Comment


class PostDocumentsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        loc = Location(
            coordinates=(37.535326868725456, 127.05448755531773),
            street_address="서울특별시 성동구 둘레15길",
            building_number=7
        )
        post = Post(
            location=loc,
            open_range=1,
            author_id=1,
            comments_on=1,
            content="아 코딩하기 시러어어ㅓㅓㅇ"
        )
        post.save()

    def test_coordinates(self):
        s = Post.search(index='musicmaps')
        result = s.execute()
        self.assertEquals(result[0].location.coordinates,[37.535326868725456, 127.05448755531773])

    def test_add_comment(self):
        s = Post.search(index='musicmaps')
        result = s.execute()
        result[0].add_comment(author_id=1, content="댓글")
        self.assertEquals(result[0].comments[0].content, "댓글")

    def test_delete_post(self):
        s = Post.search(index='musicmaps').query("match", content="아 코딩하기 시러어어ㅓㅓㅇ")
        response = s.delete()
        self.assertGreater(response.deleted, 0)