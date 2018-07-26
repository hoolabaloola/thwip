from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from comics.models import (Issue, Publisher, Series)
from comics.serializers import (ComicPageSerializer, IssueSerializer,
                                PublisherSerializer, ReaderSerializer,
                                SeriesSerializer)
from comics.tasks import import_comic_files_task


class IssueViewSet(mixins.UpdateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    get:
    Returns a list of all issues.

    retrieve:
    Returns the information of an individual issue.

    put:
    Update the leaf and status for an issues.

    get-page:
    Returns the base 64 image of the page from an issue.
    """
    queryset = (
        Issue.objects
        .select_related('series')
        .prefetch_related('credits_set')
    )
    serializer_class = IssueSerializer
    lookup_field = 'slug'

    @detail_route(url_path='get-page/(?P<page>[0-9]+)')
    def get_page(self, request, slug=None, page=None):
        issue = self.get_object()
        page_json = ComicPageSerializer(issue, many=False, context={
                                        'page_number': self.kwargs['page']})
        return Response(page_json.data)

    @detail_route()
    def reader(self, request, slug=None):
        issue = self.get_object()
        page_json = ReaderSerializer(
            issue, many=False, context={"request": request})
        return Response(page_json.data)

    @list_route()
    def import_comics(self, request):
        import_comic_files_task.apply_async()
        return Response(data={"import_comics": "Started imports."})


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    get:
    Returns a list of all publishers.

    retrieve:
    Returns the information of an individual publisher.
    """
    queryset = (
        Publisher.objects
        .prefetch_related('series_set')
    )
    serializer_class = PublisherSerializer
    lookup_field = 'slug'

    @detail_route()
    def series_list(self, request, slug=None):
        """
        Returns a list of series for a publisher.
        """
        publisher = self.get_object()
        series = (
            Series.objects
            .filter(publisher__slug=publisher.slug)
            .select_related('publisher')
            .prefetch_related('issue_set')
        )
        series_json = SeriesSerializer(
            series, many=True, context={"request": request})
        return Response(series_json.data)


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    get:
    Returns a list of all the comic series.

    retrieve:
    Returns the information of an individual comic series.
    """
    queryset = (
        Series.objects
        .select_related('publisher')
        .prefetch_related('issue_set')
    )
    serializer_class = SeriesSerializer
    lookup_field = 'slug'

    @detail_route()
    def issue_list(self, request, slug=None):
        """
        Returns a list of issues for a series.
        """
        series = self.get_object()
        issues = (
            Issue.objects
            .filter(series__slug=series.slug)
            .select_related('series')
        )
        issues_json = IssueSerializer(
            issues, many=True, context={"request": request})
        return Response(issues_json.data)
