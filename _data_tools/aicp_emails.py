from content.models import EmailTemplate

prefix = 'EXAM_APPLICATION_AICP'
aicp_suffixes = ['_INVALID_DOCUMENTS', '_REVIEW_CONFIRMATION', '_PENDING', '_INCOMPLETE', '_APPROVED',]
header = '<p>Dear {{application.contact.first_name}},</p><br>'
footer = '<p>Sincerely,</p><br><p>APA Customer Service</p><p>American Institute of Certified Planners</p><p>The American Planning Association’s Professional Institute</p><p>205 N. Michigan Ave, Suite 1200</p><p>Chicago, IL 60601</p>'
 

# Approval Email (Status: A)

approved_body_content = """
<p><span>Your {{application.exam.title}} application was approved. Please follow the steps below to register for the exam and schedule your exam appointment with Prometric. </span></p>
<ol>
	<li>Visit <a href="http://www.planning.org/certification/currentexam">www.planning.org/certification/currentexam</a>.</li>
	<li><span>Click the green link &lsquo;Begin Online Registration&rsquo;. </span></li>
	<li><span>Submit the $425 exam fee payment.</span></li>
	<li ><span>APA will email you a payment confirmation that will contain your Eligibility ID.</span></li>
	<li>Visit the <a href="http://www.prometric.com/aicp" id="aui-3-18-0-4_136110"><span id="aui-3-18-0-4_136109">Prometric website</span></a><span id="aui-3-18-0-4_136223"> to schedule your exam appointment.</span></li>
	<li><span id="aui-3-18-0-4_136115">Click on &ldquo;Schedule My Test&rdquo;.</span></li>
	<li><span id="aui-3-18-0-4_136119">Select your country and state then click &ldquo;Next&rdquo;.</span></li>
	<li">Confirm you agree with the Privacy Policy and click &ldquo;Next&rdquo;.</li>
	<li>Enter you Eligibility ID<span id="aui-3-18-0-4_136125"> (in the Candidate ID field) and the first four letters of your last name, then click &ldquo;Next&rdquo;.</span></li>
	<li><span id="aui-3-18-0-4_136127">Enter your ZIP code in the search field and click &quot;Search&quot; to locate your local</span> testing center.</li>
	<li><span id="aui-3-18-0-4_136133">Click the &quot;Schedule an Appointment&quot; link next to your preferred testing center.</span></li>
	<li><span id="aui-3-18-0-4_136137">Choose a date and time available at the testing center. Click &quot;Back&quot; to search for other dates and times at a different testing center.</span></li>
	<li><span id="aui-3-18-0-4_136141">Enter your contact information and click &quot;Next.&quot;</span></li>
	<li><span id="aui-3-18-0-4_136143">Review the exam appointment information and click &quot;Complete Appointment&quot; to</span> confirm your appointment.</li>
</ol><br>
<p><span>For questions regarding your registration, please contact us at </span><a href="mailto:aicpexam@planning.org"><span>aicpexam@planning.org</span></a>.</p><br> 
"""

# Denial Email (Status: D): No Auto Email
 

# Incomplete Email (Status: I)
incomplete_body_content = '<p>Your {{application.exam.title}} application was found to be incomplete. APA will email you with notification that explains why your application is incomplete. For questions regarding your application, please contact us at <a href="mailto:aicpexam@planning.org">aicpexam@planning.org</a>.</p><br>'


# Pending Email (Status: P)
pending_body_content = '<p>Your completed {{application.exam.title}} application has been submitted and received by APA.</p><br>'


# General Status Update Email (Status: R, V_C, V_R)
review_confirmation_body_content = '<p><span>Your {{application.exam.title}} application has been submitted for review. APA will email you with your application status by the notification deadline at www.planning.org/certification/currentexam. For questions regarding your application, please contact us at </span><a href="mailto:aicpexam@planning.org">aicpexam@planning.org</a>.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p><br>'

 
# General Status Update Email (Status: V_I)
invalid_body_content = '<p ><span>Your {{application.exam.title}} application verification document(s) are invalid. APA staff will email you with further information. Please address the concerns with your verification documents in order for your application to continue in the review process. For questions regarding your application, please contact us at </span><a href="mailto:aicpexam@planning.org">aicpexam@planning.org</a>.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p><br>' 


invalid_body = header + invalid_body_content + footer
review_confirmation_body = header + review_confirmation_body_content + footer
pending_body = header + pending_body_content + footer
incomplete_body = header + incomplete_body_content + footer
approved_body = header + approved_body_content + footer

body_list = [invalid_body, review_confirmation_body, pending_body, incomplete_body, approved_body]


def make_aicp_emails():
	for i in range(0, len(aicp_suffixes)):
		code = prefix + aicp_suffixes[i]
		title = code
		EmailTemplate.objects.update_or_create(
			code=code, 
			title=code,
		 	status='A', 
		 	email_from='aicpexam@planning.org',
		 	subject=code,
		 	body=body_list[i])

def test_make_aicp_email():
		code="EXAM_APPLICATION_AICP_TEST"
		EmailTemplate.objects.update_or_create(
			code=code, 
			title=code,
		 	status='A', 
		 	email_from='aicpexam@planning.org',
		 	subject=code,
		 	body=invalid_body)