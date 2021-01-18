# record-music-backend
Django + mongodb


## API 문서
*accounts model field 이름에 관한 주의 사항*

 * userid = user nickname에 해당함.

 * user_id = account db에 저장되어 있는 해당 user의 pk.

영문법 표기에 맞추기 위해 API response에 등장하는 userid는 user_id로 표기함.
**User계정 관련 response에 나오는 user_id 는 user의 pk가 아님!!**

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
> GET /accounts/search/{userid}
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
> GET /accounts/{userid}/followers

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
> GET /account/{userid}/following

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
> POST /accounts/{userid}/follow

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
> PUT /accounts/{userid}/unfollow

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
>  GET /accounts/{userid}/profile
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
> GET /musicmaps/{music_name}
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
        "coordinates" : (int, int),
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
        "user_id": string,
        "images": [object[Image]],
        "content": string,
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
        "user_id": string,
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
