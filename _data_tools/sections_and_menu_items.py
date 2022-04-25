from content.models import Section, MenuItem, MasterContent


def make_root_section():

	section, c = Section.objects.get_or_create(code="ROOT")
	section.title="planning.org"
	section.save()

	print("saved root section")

	nat_conf, c = MenuItem.objects.get_or_create(title="National Conference", section=section)
	nat_conf.master = MasterContent.objects.get(content_live__url="/conference/")
	nat_conf.sort_number = 0
	nat_conf.save()

	print("saved National Conference menu item")

	phoenix, c = MenuItem.objects.get_or_create(title="Phoenix", section=section)
	phoenix.master = MasterContent.objects.get(content_live__url="/conference/phoenix/")
	phoenix.sort_number = 1
	phoenix.save()

	print("saved Phoenix menu item")

	proposals, c = MenuItem.objects.get_or_create(title="Proposals", section=section)
	proposals.master = MasterContent.objects.get(content_live__url="/conference/proposal/")
	proposals.sort_number = 2
	proposals.save()

	print("saved Proposals menu item")

	plan_expo, c = MenuItem.objects.get_or_create(title="Planning Expo", section=section)
	plan_expo.master = MasterContent.objects.get(content_live__url="/conference/planningexpo/")
	plan_expo.sort_number = 3
	plan_expo.save()

	print("saved Planning Expo menu item")

	speaker, c = MenuItem.objects.get_or_create(title="Speaker Confirmation", section=section)
	speaker.master = MasterContent.objects.get(content_live__url="/conference/speaker/")
	speaker.sort_number = 4
	speaker.save()

	print("saved Speaker Confirmation menu item")

	program_2015, c = MenuItem.objects.get_or_create(title="2015 Program", section=section)
	program_2015.url = "/search/"
	program_2015.sort_number = 5
	program_2015.save()

	print("saved 2015 Program menu item")

	conf_reasons, c = MenuItem.objects.get_or_create(title="Reasons to Attend", section=section)
	conf_reasons.master = MasterContent.objects.get(content_live__url="/conference/whyattend/reasons/")
	conf_reasons.sort_number = 6
	conf_reasons.parent = nat_conf
	conf_reasons.save()

	print("saved Reasons to Attend menu item")

	conf_mentor, c = MenuItem.objects.get_or_create(title="Mentor Match", section=section)
	conf_mentor.master = MasterContent.objects.get(content_live__url="/conference/whyattend/mentormatch/")
	conf_mentor.sort_number = 7
	conf_mentor.parent = nat_conf
	conf_mentor.save()

	print("saved Mentor Match menu item")

	conf_networking, c = MenuItem.objects.get_or_create(title="Networking", section=section)
	conf_networking.master = MasterContent.objects.get(content_live__url="/conference/whyattend/networking/")
	conf_networking.sort_number = 8
	conf_networking.parent = nat_conf
	conf_networking.save()

	print("saved Networking menu item")

	conf_ceu, c = MenuItem.objects.get_or_create(title="CEU Credits", section=section)
	conf_ceu.master = MasterContent.objects.get(content_live__url="/conference/whyattend/ceu/")
	conf_ceu.sort_number = 9
	conf_ceu.parent = nat_conf
	conf_ceu.save()

	print("saved CEU Credits menu item")

	conf_future, c = MenuItem.objects.get_or_create(title="Future Conferences", section=section)
	conf_future.master = MasterContent.objects.get(content_live__url="/conference/future/")
	conf_future.sort_number = 10
	conf_future.parent = nat_conf
	conf_future.save()

	print("saved Future Conferences menu item")

	conf_previous, c = MenuItem.objects.get_or_create(title="Previous Conferences", section=section)
	conf_previous.master = MasterContent.objects.get(content_live__url="/conference/previous/")
	conf_previous.sort_number = 11
	conf_previous.parent = nat_conf
	conf_previous.save()

	print("saved Previous Conferences menu item")

	phoenix_history, c = MenuItem.objects.get_or_create(title="History/Great Places", section=section)
	phoenix_history.master = MasterContent.objects.get(content_live__url="/conference/phoenix/history/")
	phoenix_history.sort_number = 12
	phoenix_history.parent = phoenix
	phoenix_history.save()

	print("saved History/Great Places menu item")

	pheonix_travel, c = MenuItem.objects.get_or_create(title="Travel", section=section)
	pheonix_travel.master = MasterContent.objects.get(content_live__url="/conference/phoenix/travel/")
	pheonix_travel.sort_number = 13
	pheonix_travel.parent = phoenix
	pheonix_travel.save()

	print("saved Travel menu item")

	phoenix_fun, c = MenuItem.objects.get_or_create(title="Fun Facts", section=section)
	phoenix_fun.master = MasterContent.objects.get(content_live__url="/conference/phoenix/funfacts/")
	phoenix_fun.sort_number = 14
	phoenix_fun.parent = phoenix
	phoenix_fun.save()

	print("saved Fun Facts menu item")

	pheonix_media, c = MenuItem.objects.get_or_create(title="Media and News", section=section)
	pheonix_media.master = MasterContent.objects.get(content_live__url="/conference/seattle/news/")
	pheonix_media.sort_number = 15
	pheonix_media.parent = phoenix
	pheonix_media.save()

	print("saved Media and News menu item")

	proposal_how, c = MenuItem.objects.get_or_create(title="How to Submit a Proposal", section=section)
	proposal_how.master = MasterContent.objects.get(content_live__url="/conference/proposal/howto/")
	proposal_how.sort_number = 16
	proposal_how.parent = proposals
	proposal_how.save()

	print("saved How to Submit a Proposal menu item")

	proposal_tips, c = MenuItem.objects.get_or_create(title="Tips for Successful Proposals", section=section)
	proposal_tips.master = MasterContent.objects.get(content_live__url="/conference/proposal/tips/")
	proposal_tips.sort_number = 17
	proposal_tips.parent = proposals
	proposal_tips.save()

	print("saved Tips for Successful Proposals menu item")

	proposal_sample, c = MenuItem.objects.get_or_create(title="Sample Accepted Proposals", section=section)
	proposal_sample.master = MasterContent.objects.get(content_live__url="/conference/proposal/sample/")
	proposal_sample.sort_number = 18
	proposal_sample.parent = proposals
	proposal_sample.save()

	print("saved Sample Accepted Proposals menu item")

	proposal_tracks, c = MenuItem.objects.get_or_create(title="Tracks", section=section)
	proposal_tracks.master = MasterContent.objects.get(content_live__url="/conference/program/tracks/")
	proposal_tracks.sort_number = 19
	proposal_tracks.parent = proposals
	proposal_tracks.save()

	print("saved Tracks menu item")

	expo_exhibitors, c = MenuItem.objects.get_or_create(title="Exhibitors", section=section)
	expo_exhibitors.master = MasterContent.objects.get(content_live__url="/conference/planningexpo/exhibitors/")
	expo_exhibitors.sort_number = 20
	expo_exhibitors.parent = plan_expo
	expo_exhibitors.save()

	print("saved Exhibitors menu item")

	expo_map, c = MenuItem.objects.get_or_create(title="Exhibit Hall Map", section=section)
	expo_map.url = "/conference/planningexpo/exhibitors/#Map"
	expo_map.sort_number = 21
	expo_map.parent = plan_expo
	expo_map.save()

	print("saved Exhibit Hall Map menu item")

	speaker_policy, c = MenuItem.objects.get_or_create(title="Speaker Policies", section=section)
	speaker_policy.master = MasterContent.objects.get(content_live__url="/conference/speaker/policies/")
	speaker_policy.sort_number = 22
	speaker_policy.parent = speaker
	speaker_policy.save()

	print("saved Speaker Policies menu item")




