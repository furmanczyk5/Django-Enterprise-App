from statistics import mean
from django.db.models import Q
from comments.models import ExtendedEventEvaluation




def UpdateEvaluationRating(eval):
    ratings = []
    if eval.objective_rating:
        ratings.append(eval.objective_rating)

    if eval.value_rating:
        ratings.append(eval.value_rating)

    if eval.knowledge_rating:
        ratings.append(eval.knowledge_rating)

    if eval.practice_rating:
        ratings.append(eval.practice_rating)


    # speaker rating is zero if N/a
    if eval.speaker_rating != 0:
        ratings.append(eval.speaker_rating)

    print(ratings)
    if len(ratings):
        eval.rating = mean(ratings)
        eval.save()




if __name__ == "__main__":
    # eval = ExtendedEventEvaluation.objects.filter(rating__isnull=True).order_by('-created_time').first()
    for eval in ExtendedEventEvaluation.objects.filter(rating__isnull=True).filter(Q(objective_rating__isnull=False) | Q(
                    value_rating__isnull=False) | Q(knowledge_rating__isnull=False) | Q(
                    practice_rating__isnull=False) | Q(speaker_rating__isnull=False)):
        print(eval)
        UpdateEvaluationRating(eval)


