import factory
from django_comments.models import Comment
from .models import CommentTestArticle
from kawaz.core.personas.tests.factories import PersonaFactory

class CommentTestArticleFactory(factory.DjangoModelFactory):

    class Meta:
        model = CommentTestArticle

    text = '本文です'
    author = factory.SubFactory(PersonaFactory)


class CommentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Comment

    comment = "コメントだよー"
    user = factory.SubFactory(PersonaFactory)
    content_object = factory.SubFactory(CommentTestArticleFactory)
    site_id = 1
