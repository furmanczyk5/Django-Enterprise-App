from content.models import MessageText

# LOGIN ERROR MESSAGES

msg_texts = ("<p>Please log in to the APA website before proceeding to that page.</p>",
             "We’re sorry, you must belong to APA and the members-only Planners’ Advocacy Network to view that page and other exclusive content. If you are an APA member, you can sign up for the Network from My APA. If you are not an APA member, please join us! We’d love to have you.",
             "We’re sorry, you must be a member of the American Institute of Certified Planners to view that page. Learn about AICP and the advantages of certification.",
             "We’re sorry, but you do not have an active CM log. Let’s figure out what to do next.",
             "Your CM log may not be set up yet. Please contact AICP member service at 202-349-1016 or submit a request to AICP CM through our customer service form for assistance.",
             "Please contact AICP member service at 202-349-1016 or or submit a request to AICP CM through our customer service form for assistance.",
             "Please submit a request to membership through our customer service form for assistance making a dues payment.",
             "Please contact AICP member service at 202-349-1016 or submit a request to AICP CM through our customer service form for assistance.",
             "We’re sorry, but only subscribers may view that page. Learn more about the APA Knowledge Center and our subscription services.",
             "We’re sorry, but you are not registered for APA’s National Planning Conference. Register now.",
             "We’re sorry, but you must be a member of the division to view that page. Please join us! We’d love to have you.",
             "We’re sorry, but you must be a member of the chapter to view that page. Your APA chapter membership is determined by your Home address.",
             )

msg_codes = ("LOGIN_NOT_ALLOWED",
             "NOT_APA_MEMBER",
             "NOT_AICP_MEMBER",
             "NO_ACTIVE_CM_LOG",
             "NEW_AICP_MEMBER",
             "AICP_MEMBERSHIP_LAPSED_REQUIREMENTS",
             "AICP_MEMBERSHIP_LAPSED_DUES",
             "AICP_ERRONEOUS_DENIAL",
             "NOT_SUBSCRIBER",
             "NOT_REGISTERED",
             "NOT_DIVISION_MEMBER",
             "NOT_CHAPTER_MEMBER"
             )

msg_titles = ("not logged in",
              "logged in, but not an APA member",
              "logged in, but not an AICP member",
              "logged in, but can’t see CM log",
              "logged in, but can’t see CM log: new AICP member",
              "logged in, but can’t see CM log: AICP membership has lapsed (requirements)",
              "logged in, but can’t see CM log: AICP membership has lapsed (unpaid dues)",
              "logged in, but can’t see CM log: (erroneous denial)",
              "logged in, but not a subscriber",
              "logged in, but not registered",
              "logged in, but not a division member",
              "logged in, but not a chapter member"
              )

msg_data = (
    ("LOGIN_NOT_ALLOWED",
     '<p>Please <a href="http://conference.planning.org/myapa/">log in</a> to the APA website before proceeding to that page.</p>',
     "not logged in"),

    ("NOT_APA_MEMBER",
     '<p><span style="font-size:12.0pt;font-family:Calibri;mso-fareast-font-family:Calibri;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-ansi-language:EN-US;mso-fareast-language:EN-US;mso-bidi-language:AR-SA">We&rsquo;re sorry, you must belong to APA and the members-only Planners’ Advocacy Network to view that page and other exclusive content. If you are an APA member, you can <a href="http://www.planning.org/myapa/profile/#planners-advocacy-network">sign up for the Network from My APA. </a> If you are not an APA member,<a href="http://www.planning.org/join/">please join us</a>! We&rsquo;d love to have you.</span></p>',
     "logged in, but not an APA member"),

    ("NOT_AICP_MEMBER",
     '<p style="margin-left:.5in;">We&rsquo;re sorry, you must be a member of the American Institute of Certified Planners to view that page. <a href="http://www.planning.org/aicp/">Learn about AICP and the advantages of certification</a>.</p>',
     "logged in, but not an AICP member"),

    ("NO_ACTIVE_CM_LOG",
     '''<p style="margin-left:.5in;">We&rsquo;re sorry, but you do not have an active CM log. Let&rsquo;s figure out what to do next.</p><u\nl><li><strong>If you are a new AICP member and this is your first time accessing your CM log</strong></li></ul><p style="margin-lef\nt:1.0in;">Your CM log may not be set up yet. Please contact AICP member service at 202-349-1016 or submit a request to AICP CM through our customer service form for assistance.</p><ul><li><strong>If your AICP membership \nhas lapsed because of failure to fulfill CM requirements in a previous reporting period </strong></li></ul><p style="margin-left:1.\n0in;">Please contact AICP member service at 312-431-9100 or submit a request to AICP CM through our customer service form for assistance.</p><ul><li><strong>If your AICP membership has lapsed because of unpaid dues </str\nong></li></ul><p style="margin-left:1.0in;">Please contact APA customer service at 312-431-9100 or submit a request to membership through our customer service form for assistance making a dues payment.</p><ul><li><strong>If none of these apply and you believe yo\nu received this message in error</strong></li></ul><p>Please contact AICP member service at 202-349-1016 or submit a request to AICP CM through our customer service form for assistance.</p>''',
     "logged in, but can’t see CM log"),

    ("NOT_SUBSCRIBER",
     '<p><span style="font-size:12.0pt;font-family:Calibri;mso-fareast-font-family:Calibri;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-ansi-language:EN-US;mso-fareast-language:EN-US;mso-bidi-language:AR-SA">We&rsquo;re sorry, but only subscribers may view that page. Learn more about the <a href="http://www.planning.org/knowledgecenter/">APA Knowledge Center</a> and our subscription services.</span></p>',
     "logged in, but not a subscriber"),

    ("NOT_REGISTERED",
     '<p><span style="font-size:12.0pt;font-family:Calibri;mso-fareast-font-family:Calibri;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-ansi-language:EN-US;mso-fareast-language:EN-US;mso-bidi-language:AR-SA">We&rsquo;re sorry, but you are not registered for APA&rsquo;s <a href="http://www.planning.org/conference/">National Planning Conference</a>. <a href="http://conference.planning.org/conference/registration/">Register now</a>.</span></p>',
     "logged in, but not registered"),

    ("NOT_DIVISION_MEMBER",
     '<p><span style="font-size:12.0pt;font-family:Calibri;mso-fareast-font-family:Calibri;mso-bidi-font-family:&quot;Times New Roman&quot;;mso-ansi-language:EN-US;mso-fareast-language:EN-US;mso-bidi-language:AR-SA">We&rsquo;re sorry, but you must be a member of the division to view that page. <a href="http://www.planning.org/divisions/">Please join us</a>! We&rsquo;d love to have you.</span></p>',
     "logged in, but not a division member"),

    ("NOT_CHAPTER_MEMBER",
     '<p style="margin-left:.5in;">We&rsquo;re sorry, but you must be a member of the chapter to view that page. Your APA chapter membership is determined by your primary address.</p><p style="margin-left:.5in;">&nbsp;</p><ul><li>If you are an APA member and you recently moved to a different state, please contact APA customer service for assistance at 312-431-9100 or email <a href="mailto:customerservice@planning.org">customerservice@planning.org</a></li></ul><p style="margin-left:69.35pt;">&nbsp;</p><p>To purchase an additional chapter membership, click here &lt;link T.K.&gt;</p>',
     "logged in, but not a chapter member"),
)


def make_msg_text_objects():
    for i in range(0, len(msg_data)):
        MessageText.objects.get_or_create(code=msg_data[i][0], text=msg_data[i][1], title=msg_data[i][2],
                                          message_level=2, message_type='EMBEDDED')
