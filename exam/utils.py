from .models import Exam


def build_exams_list():
    exams = Exam.objects.all()
    exam_codes = [e.code for e in exams]
    l = [(c, c) for c in exam_codes]
    l.append(("_ALL", "All Exams"))
    return l
