import time

from elasticsearch_dsl import Q, MultiSearch, Search
from elasticsearch.exceptions import ConflictError
from musicmaps.documents import Post


def get_music_maps_geo(coordinates):
    s = Post.search(index='musicmaps').filter({
        'geo_distance': {
            "distance": coordinates.get("distance"),
            "coordinates":
                {"lat": coordinates.get("lat"),
                 "lon": coordinates.get("lon")}
        }
    })
    return s.execute()


def create_music_maps(data):
    post = Post(
        open_range=data['open_range'],
        author_id=data['author_id'],
        comments_on=data['comments_on'],
        content=data['content'],
        coordinates=data['coordinates'],
        street_address=data['address'],
        building_number=data['build_num']
    )
    return post.save()


def update_music_maps(data):
    post = Post.get(id=data['id'])
    if post is not None:
        return post.update(
            open_range=data['open_range'],
            comments_on=data['comments_on'],
            content=data['content'],
            coordinates=data['coordinates'],
            street_address=data['address'],
            building_number=data['build_num'],
            retry_on_conflict=5
        )
    else:
        return 404


def delete_music_maps(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            return post.delete()
        except ConflictError:
            time.sleep(1)
            return delete_music_maps(data)
    else:
        return 404


def add_comment(data):
    post = Post.get(id=data['id'])
    if post is not None and post.comments_on:
        try:
            post.add_comment(data['author_id'], data['content'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return add_comment(data)
    else:
        return 404


def update_comment(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            post.update_comment(data['author_id'], data['content'], data['index'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return update_comment(data)
    else:
        return 404


def delete_comment(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            post.delete_comment(data['author_id'], data['index'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return delete_comment(data)
    else:
        return 404


def location_search(data):
    s = Post.search(index='musicmaps').query('match', street_address__nori=data['query'])
    res = s.execute().to_dict()['hits']['hits']
    if len(res) == 0:
        return 404

    return res


def music_search(data):
    q = Q(
        {"nested": {
            "path": "playlist",
            "query": {
                "match": {
                    "playlist.name.nori": data['query']
                }
            }
        }
        })
    s = Post.search(index='musicmaps').query(q)
    res = s.execute().to_dict()['hits']['hits']
    if len(res) == 0:
        return 404

    return res


def total_search(data: dict):
    q = Q(
        {"nested": {
            "path": "playlist",
            "query": {
                "match": {
                    "playlist.name.nori": data['query']
                }
            }
        }
        })
    ms = MultiSearch(index='musicmaps')
    ms = ms.add(Search().query('match', street_address__nori=data['query']))
    ms = ms.add(Search().query(q))
    res = ms.execute()

    res = [doc.to_dict()['hits']['hits'] for doc in res]
    res = res[0] + res[1]

    res = list({doc['_id']: doc for doc in res}.values())

    if len(res) == 0:
        return 404

    return res
