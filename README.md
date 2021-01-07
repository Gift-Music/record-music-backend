# record-music-backend
Django + mongodb


## API 문서

### User login
1. 일반 로그인(ID, PW)
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
3. Refresh후 로그인
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
- request
``` json
    {
        "user_id":string
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

### Following 조회
- request
``` json
    {
        "user_id":string
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

### User Follow
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
        None
    }
```

### User UnFollow
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
        None
    }
```

### User Profile 조회
- request
``` json
    {
        "user_id": string
    }
```
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
- request
``` json
    {
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
3. 사용자
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

### MusicMaps 수정

### MusicMaps 삭제

### Push

