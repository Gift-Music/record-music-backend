from django.utils import timezone
from djongo import models
from accounts.models import User


class Image(models.Model):
    image = models.ImageField()

    class Meta:
        abstract = True


class IntegerValue(models.Model):
    integer = models.IntegerField()

    class Meta:
        abstract = True


class Location(models.Model):
    type = models.CharField(max_length=100)
    coordinates = models.ArrayField(IntegerValue)

    class Meta:
        abstract = True


class Music(models.Model):
    track_number = models.IntegerField()
    artists = models.CharField(max_length=100)
    album_cover = models.ImageField()
    name = models.CharField(max_length=100)
    album = models.CharField(max_length=100)


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    comments = models.ArrayReferenceField(
        to="self",
        on_delete=models.CASCADE
    )


class MusicMaps(models.Model):
    class OpenRange(models.IntegerChoices):
        PUBLIC = 0, 'Public'
        FOLLOW = 1, 'Follow'
        FOLLOW_BACK = 2, 'Follow Back' # 맞팔로우
        PRIVATE = 4, 'Private'

    images = models.ArrayField(
        model_container=Image
    )
    content = models.TextField()
    date_created = models.DateTimeField(
        verbose_name='Date Created',
        default=timezone.now
    )
    date_updated = models.DateTimeField(
        verbose_name='Date Updated',
        default=timezone.now
    )
    open_range = models.IntegerField(
        choices=OpenRange.choices
    )
    comments_on = models.BooleanField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author'
    )
    memorize_users = models.ArrayReferenceField(
        to=User,
        on_delete=models.CASCADE,
        related_name='memorize_users'
    )
    location = models.EmbeddedField(
        model_container=Location
    )
    comments = models.ArrayReferenceField(
        to=Comment,
        on_delete=models.CASCADE
    )
    playlist = models.ArrayReferenceField(
        to=Music,
        on_delete=models.CASCADE
    )
    street_address = models.CharField(max_length=200)
    building_number = models.CharField(max_length=30)

    class Meta:
        ordering = ("date_updated",)

    @property
    def memorize_count(self):
        return self.memorize_users.all().count()

    @property
    def comments_count(self):
        return self.comments.all().count()


    #     indexes = [
    #         TwoDSphereIndex(fields=['location'])
    #     ] optimization for search by location
    # if service going to be heavy Use this code and
