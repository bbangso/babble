from django.shortcuts import render, get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TagListSerializer, PhotoListSerializer, PhotoDetailSerializer, PhotoCommentSerializer, AlbumListSerializer, AlbumDetailSerializer

from .models import Tag, Photo, PhotoComment, PhotoTag, Album, AlbumPhotoRelationship, AlbumTag
# Create your views here.

class TagListView(APIView):
    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagListSerializer(tags, many=True)
        return Response(serializer.data) 

class PhotoListView(APIView):
    # 아기의 전체 사진 조회
    def get(self, request):
        cb = request.user.current_baby
        if not cb:
            raise ValueError('아이를 생성하거나 선택해주세요.')
        photos = Photo.objects.filter(baby=cb).order_by('-last_modified')
        serializer = PhotoListSerializer(photos, many=True)
        return Response(serializer.data)

    # 아기 사진 업로드
    def post(self, request):
        cb = request.user.current_baby.id
        if not cb:
            raise ValueError('아이를 생성하거나 선택해주세요.')
        
        new_photos = request.data
        for photo in new_photos:
            photo["baby"] = cb
            serializer = PhotoDetailSerializer(data=photo)
            if serializer.is_valid(raise_exception=True):
                created_photo = serializer.save(creator=request.user, modifier=request.user)
            # tag
            for tag_name in photo['tags']:
                try:
                    tag = Tag.objects.get(tag_name=tag_name)
                except:
                    tag = Tag(tag_name=tag_name)
                    tag.save()
                PhotoTag(tag=tag, photo=created_photo).save()
        return Response({"message":"사진이 등록되었습니다."})

class PhotoDetailView(APIView):
    # 특정 사진 디테일 정보 조회
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        if request.user.current_baby == photo.baby:
            serializer = PhotoDetailSerializer(photo)
            return Response(serializer.data)
        else:
            raise ValueError('해당 사진을 가져올 수 없습니다.')
    
    # 특정 사진 디테일 정보 수정
    def put(self, request, photo_id):
        cb = request.user.current_baby.id
        if not cb:
            raise ValueError('아이를 생성하거나 선택해주세요.')
        photo = get_object_or_404(Photo, id=photo_id)
        request.data["baby"] = cb
        # 여기서 권한 검증이 한 번 들어가줘야함
        serializer = PhotoDetailSerializer(photo, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(modifier=request.user)
            
            photo.photo_tags.clear()
            for tag_name in request.data['tags']:
                try:
                    tag = Tag.objects.get(tag_name=tag_name)
                except:
                    tag = Tag(tag_name=tag_name)
                    tag.save()
                PhotoTag(tag=tag, photo=photo).save()

            return Response(serializer.data)
        return Response(serializer.errors)

    # 특정 사진 삭제
    def delete(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        # 여기서 권한 검증이 한 번 들어가줘야함 
        photo.delete()
        return Response({"message":"사진이 삭제되었습니다."})


class PhotoCommentListView(APIView):
    # 사진 댓글 리스트 조회
    def get(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        serializer = PhotoCommentSerializer(photo.comments.order_by('-create_date'), many=True)
        return Response(serializer.data)

    # 사진 댓글 생성
    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        serializer = PhotoCommentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user, photo=photo)
        return Response(serializer.data)


class PhotoCommentDetailView(APIView):
    # 사진 댓글 수정
    def put(self, request, photo_id, comment_id):
        comment = get_object_or_404(PhotoComment, id=comment_id)
        # 여기서 권한 검증이 한 번 들어가줘야함
        if comment.user.id == request.user.id:
            serializer = PhotoCommentSerializer(comment, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors)
        else:
            return Response({"message": "작성자만 수정할 수 있습니다."}, status=400)

    # 사진 댓글 삭제
    def delete(self, request, photo_id, comment_id):
        comment = get_object_or_404(PhotoComment, id=comment_id)
        if comment.user.id == request.user.id:
            comment.delete()
            return Response({"message":"댓글이 삭제되었습니다."}, status=200)
        else:
            return Response({"message": "작성자만 삭제할 수 있습니다."}, status=400)


class PhotoSearchView(APIView):
    def post(self, request):
        keyword = request.data["keyword"]
        cb = request.user.current_baby.id
        if not cb:
            raise ValueError('아이를 생성하거나 선택해주세요.')
        searched_photos = Photo.objects.none()
        tags = Tag.objects.filter(tag_name__icontains=keyword)
        for tag in tags:
            searched_photos = searched_photos | tag.tagged_photos.all()
        searched_photos = searched_photos.filter(baby=cb)
        serializer = PhotoListSerializer(searched_photos, many=True)
        return Response(serializer.data)


class AlbumListView(APIView):
    # 전체 앨범 목록 가져오기
    def get(self, request):
        baby = request.user.current_baby
        albums = Album.objects.filter(baby=baby).order_by('-create_date')
        serializer = AlbumListSerializer(albums, many=True)
        return Response(serializer.data)

    # 새 앨범 생성
    def post(self, request):
        baby = request.user.current_baby
        data = {
            'album_name': request.data['album_name']
        }
        serializer = AlbumDetailSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            created_album = serializer.save(baby=baby, creator=request.user)

            # 만약 tags들이 있는 경우 태그 정보 저장 
            if request.data['tags']:
                for tag_name in request.data['tags']:
                    try:
                        tag = Tag.objects.get(tag_name=tag_name)
                    except:
                        tag = Tag(tag_name=tag_name)
                        tag.save()
                    AlbumTag(tag=tag, album=created_album).save()

            # 만약 photos들이 있는 경우 사진 정보 저장 
            if request.data['photos']:
                for photo_id in request.data['photos']:
                    photo = get_object_or_404(Photo, id=photo_id)
                    album_photo = AlbumPhotoRelationship(album=created_album, photo=photo)
                    album_photo.save()
                # 첫번째 사진을 cover_photo로 지정
                created_album.cover_photo = get_object_or_404(Photo, id=request.data['photos'][0]).image_url
                created_album.save()

            return Response(serializer.data)
        return Response(serializer.errors)


class AlbumDetailView(APIView):
    # 특정 앨범 내의 사진들 가져오기
    def get(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        serializer = AlbumDetailSerializer(album)
        return Response(serializer.data)

    # 앨범 정보(앨범명, 태그) 수정
    def put(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        serializer = AlbumDetailSerializer(album, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            # 태그 정보 수정하는 경우
            if request.data['tags']:
                album.album_tags.clear()
                for tag_name in request.data['tags']:
                    try:
                        tag = Tag.objects.get(tag_name=tag_name)
                    except:
                        tag = Tag(tag_name=tag_name)
                        tag.save()
                    AlbumTag(tag=tag, album=album).save()

            return Response(serializer.data)
        return Response(serializer.errors)

    # 앨범 삭제
    def delete(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        album.delete()
        return Response({"message":"앨범이 삭제되었습니다."})


class AlbumPhotoView(APIView):
    # 앨범에 사진 추가
    def post(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        for photo_id in photos:
            photo = get_object_or_404(Photo, id=photo_id)
            album_photo = AlbumPhotoRelationship(album=album, photo=photo)
            album_photo.save()
        return Response({"message":"사진(들)이 앨범에 추가되었습니다."})

    # 앨범에서 사진 삭제
    def delete(self, request, album_id):
        album = get_object_or_404(Album, id=album_id)
        for photo_id in photos:
            photo = get_object_or_404(Photo, id=photo_id)
            album_photo = get_object_or_404(AlbumPhotoRelationship, album=album, photo=photo)
            album_photo.delete()
        return Response({"message":"사진(들)이 앨범에서 삭제되었습니다."})

    