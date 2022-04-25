from datetime import datetime
from _data_tools.solr_reindex import reindex

from publications.models import Book, EBook
from store.models import ProductPrice
from events.models import Course

def books_add_prices_to_solr(reset=False):

	print("Updating prices for all Books...")

	if reset == True:
		ProductPrice.objects.filter(
			product__content__content_type="PUBLICATION", 
			product__content__resource_type="BOOK"
		).update(include_search_results=False)

	ProductPrice.objects.filter(
		product__content__content_type="PUBLICATION", 
		product__content__resource_type="BOOK",
		status="A"
	).exclude(
		end_time__lt=datetime.now()
	).update(include_search_results=True)

	print("...Reindexing all Books...")
	reindex(Book, delete_kwargs={ "query":"content_type:PUBLICATION AND resource_type:BOOK" })

def ebooks_add_prices_to_solr(reset=False):

	print("Updating prices for all Ebooks...")

	if reset == True:
		ProductPrice.objects.filter(
			product__content__content_type="PUBLICATION", 
			product__content__resource_type="EBOOK"
		).update(include_search_results=False)

	ProductPrice.objects.filter(
		product__content__content_type="PUBLICATION", 
		product__content__resource_type="EBOOK",
		status="A"
	).exclude(
		end_time__lt=datetime.now()
	).update(include_search_results=True)

	print("...Reindexing all Ebooks...")
	reindex(EBook, delete_kwargs={ "query":"content_type:PUBLICATION AND resource_type:EBOOK" })

def courses_add_prices_to_solr(reset=False):

	print("Updating prices for all Courses...")

	if reset == True:
		ProductPrice.objects.filter(
			product__content__content_type="EVENT", 
			product__content__event__event_type="COURSE"
		).update(include_search_results=False)

	ProductPrice.objects.filter(
		product__content__content_type="EVENT", 
		product__content__event__event_type="COURSE",
		status="A"
	).exclude(
		end_time__lt=datetime.now()
	).update(include_search_results=True)

	print("...Reindexing all Courses...")
	reindex(Course, delete_kwargs={ "query":"content_type:EVENT AND event_type:COURSE" })