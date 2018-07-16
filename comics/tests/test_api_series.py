from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from comics.models import Series, Publisher, Issue
from comics.serializers import SeriesSerializer


issue_date = timezone.now().date()
mod_time = timezone.now()


class GetAllSeriesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        publisher_obj = Publisher.objects.create(
            name='DC Comics', slug='dc-comics')
        super_obj = Series.objects.create(cvid='1234', cvurl='http://1.com',
                                          name='Superman', slug='superman',
                                          publisher=publisher_obj)
        batman_obj = Series.objects.create(cvid='4321', cvurl='http://2.com',
                                           name='Batman', slug='batman', publisher=publisher_obj)
        # Need to create the issues so the series image serializer doesn't kick up an error.
        Issue.objects.create(cvid='1234', cvurl='http://1.com', slug='superman-1',
                             file='/home/a.cbz', mod_ts=mod_time, date=issue_date, number='1',
                             series=super_obj, image="image/issues/super.jpg")
        Issue.objects.create(cvid='4321', cvurl='http://2.com', slug='batman-1',
                             file='/home/b.cbz', mod_ts=mod_time, date=issue_date, number='1',
                             series=batman_obj, image="image/issues/bat.jpg")

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('api:series-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class GetSingleSeriesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        factory = APIRequestFactory()
        request = factory.get('/')

        cls.serializer_context = {
            'request': Request(request),
        }

        publisher_obj = Publisher.objects.create(name='Marvel', slug='marvel')
        cls.thor = Series.objects.create(cvid='1234', cvurl='https://comicvine.com',
                                         name='The Mighty Thor', slug='the-mighty-thor',
                                         publisher=publisher_obj)
        Issue.objects.create(cvid='4321', cvurl='http://2.com', slug='thor-1',
                             file='/home/b.cbz', mod_ts=mod_time, date=issue_date, number='1',
                             series=cls.thor, image="image/issues/bat.jpg")

    def test_get_valid_single_series(self):
        resp = self.client.get(
            reverse('api:series-detail', kwargs={'slug': self.thor.slug}))
        series = Series.objects.get(slug=self.thor.slug)
        serializer = SeriesSerializer(series, context=self.serializer_context)
        self.assertEqual(resp.data, serializer.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_invalid_single_series(self):
        response = self.client.get(
            reverse('api:series-detail', kwargs={'slug': 'airboy'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
