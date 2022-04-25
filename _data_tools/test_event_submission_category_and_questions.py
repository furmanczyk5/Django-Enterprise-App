from submissions.models import Category, Question

def make_submission_category_and_questions():
	"""
	Running this will create the submissision category for Events
	"""
	# MAKE EXAMPLE QUESTIONS
	submission_question_0, is_created_0 = Question.objects.get_or_create(code="TEST_QUESTION_UNIQUE_CODE_0")
	submission_question_0.title = "What is your favorite color?"
	submission_question_0.question_type = "SHORT_TEXT"
	submission_question_0.help_text = "Don't get it wrong! This field is required"
	submission_question_0.required = True
	submission_question_0.save()

	submission_question_1, is_created_1 = Question.objects.get_or_create(code="TEST_QUESTION_UNIQUE_CODE_1")
	submission_question_1.title = "I agree to check this checkbox."
	submission_question_1.question_type = "CHECKBOX"
	submission_question_1.help_text = "This field is required, so you have to check it before you do a final submit"
	submission_question_1.required = True
	submission_question_1.save()

	submission_question_2, is_created_2 = Question.objects.get_or_create(code="TEST_QUESTION_UNIQUE_CODE_2")
	submission_question_2.title = "What is the meaning of life?"
	submission_question_2.question_type = "LONG_TEXT"
	submission_question_2.help_text = "This is not required, so leave it blank if you want"
	submission_question_2.required = False
	submission_question_2.save()

	# MAKE SUBMISSION CATEGORY
	submission_category, is_created = Category.objects.get_or_create(content_type="EVENT", code="EVENT")
	submission_category.title = "Event Submission"
	submission_category.save()

	submission_category.questions.add(submission_question_0, submission_question_1, submission_question_2)

	return "Great Success!"