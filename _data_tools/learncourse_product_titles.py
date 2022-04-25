

from learn.models import LearnCourse
from store.models import ProductLearnCourse


def add_titles_to_product():
    for product in ProductLearnCourse.objects.all():
        if product.title is None:
            try:
                lc = LearnCourse.objects.get(code = product.code, publish_status = 'PUBLISHED')
                print(lc.code, '\t\t', lc.title)
                product.title = lc.title
                product.save()
            except LearnCourse.DoesNotExist:
                print("\t\tNo corresponding published Learn Course")

if __name__ == "__main__":
    add_titles_to_product()
