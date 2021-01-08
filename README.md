# record-music-backend
Django + mongodb


## API 문서

### User login
1. 일반 로그인(ID, PW)
> POST /accounts/login
- request
``` json
    {
        "email":string,
        "password":string
    }
```
- response
``` json
    {
        "token":string,
        "user":{
            "profile_image": object[Image],
            "user_id":string,
            "email": string
        }
    }
```

2. JWT verify
> POST /accounts/verify
- request
``` json
    {
        "token": string
    }
```
- response
``` json
    {
        "token": string,
        "user":{
            "profile_image": object[Image],
            "user_id":string,
            "email": string
        }
    }
```
3. Refresh
> POST /accounts/refresh
- request
``` json
    {
        "token": string
    }
```
- response
``` json
    {
        "token": string,
        "user":{
            "profile_image": object[Image],
            "user_id":string,
            "email": string
        }
    }
```

### User registration
> POST /accounts/register
- request
``` json
    {
        "user_id" : string,
        "email" : string,
        "password" : string,
        "username" : string
    }
```
- response
``` json
    {
        "email" : string,
        "password" : string
    }
```

### User 검색
> GET /accounts/{user_id}
- request
``` json
    {
        "user_id":string,
        "username": string
    }
```
- response
``` json
    {
        "user_list":[
            {
                "profile image" : object[Image],
                "user_id" : string,
                "username" : string
            }
        ]
    }
```                          

### Follower 조회
> GET /accounts/{user_id}/followers

- response
``` json
    {
        "user_list":[
            {
                "profile image" : object[Image],
                "user_id" : string,
                "username" : string
            }
        ]
    }
```     

### Following 조회
> GET /account/{user_id}/following

- response
``` json
    {
        "user_list":[
            {
                "profile image" : object[Image],
                "user_id" : string,
                "username" : string
            }
        ]
    }
```

### User Follow
> POST /accounts/{user_id}/follow

> 신청
- request
``` json
    {
        "user_id":string
    }
```
- response
``` json
    {
        "isSuccess": boolean
    }
```

### User UnFollow
> POST /accounts/{user_id}/unfollow

> 신청
- request
``` json
    {
        "user_id":string
    }
```
- response
``` json
    {
        "isSuccess": boolean
    }
```

### User Profile 조회
>  GET /accounts/{user_id}/profile
- response
``` json
    {
        "profile_image": object[Image],
        "user_id": string,
        "user_name":string,
        "MusicMapsList": [object[MusicMaps]],
        "MusicMapsCount": int,
        "condition_message": string
    }
```


### MusicMaps 가져오기

1. 음악
> GET /musicmpas/{music_name}
- request
 ``` json
    {
        "music_name" : string,
        "coordiantes" : (int, int),
        "user_id" : string
    }
 ```
- response
``` json
    {
        "music_map_list":[
            {
                "images":[object[Music]],
                "last_update":timestamp,
                "location": object[Location],
                "open_range": int,
                "author": object_id[User],
                "memorize_count":int,
                "comments_count":int,
                "playlist":[object[Music]]
            }
        ]
    }
```
2. 장소
> GET /musicmaps/list
- request
``` json
    {
        "coordiantes" : (int, int),
        "street_addr":string,
        "building_num":string,
        "user_id" : string
    }
```
- response
``` json
    {
        "music_map_list":[
            {
                "images":[object[Music]],
                "last_update":timestamp,
                "location": object[Location],
                "open_range": int,
                "author": object_id[User],
                "memorize_count":int,
                "comments_count":int,
                "playlist":[object[Music]]
            }
        ]
    }
```
1. 사용자
> GET /musicmaps/{user_id}
- request
``` json
    {
        "user_id": string
    }
```
- response
``` json
    {
        "music_map_list":[
            {
                "images":[object[Music]],
                "last_update":timestamp,
                "location": object[Location],
                "open_range": int,
                "author": object_id[User],
                "memorize_count":int,
                "comments_count":int,
                "playlist":[object[Music]]
            }
        ]
    }
```


### MusicMaps 게시
> POST /musicmaps/{user_id}
- request
```json
    {
        "user_id": stirng,
        "images": [object[Image]],
        "content": stiring,
        "coordinates":(int, int),
        "street_addr":string,
        "build_num":string,
        "open_ragne":int,
        "playlist":[object[Music]]
    }
```
- response
```json
    {
        "isSuccess": boolean
    }
```

### MusicMaps 수정
> PUT /musicmaps/{user_id}/{musicmaps_id}
- request
```json
    {
        "user_id": stirng,
        "images": [object[Image]],
        "content": stiring,
        "coordinates":(int, int),
        "street_addr":string,
        "build_num":string,
        "open_ragne":int,
        "playlist":[object[Music]]
    }
```
- response
```json
    {
        "isSuccess": boolean
    }
```

### MusicMaps 삭제
> DELETE /musicmaps/{user_id}/{musicmaps_id}
- response
```json
    {
        "isSuccess": boolean
    }
```

### Push
나중에 생각
