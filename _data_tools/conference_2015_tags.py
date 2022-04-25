import django
django.setup()

from content.models import TagType, Tag

def create_tags():
    tag_type, created = TagType.objects.get_or_create(code='EVENTS_NATIONAL_TYPE')
    tag_type.title = 'Conference: Activity Type'
    tag_type.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='SESSION')
    tag.title = 'Sessions'
    tag.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='FACILITATED_DISCUSSION')
    tag.title = 'Facilitated Discussions'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='POSTER')
    tag.title = 'Posters'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='DEEP_DIVE')
    tag.title = 'Deep Dives'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='KEYNOTE')
    tag.title = 'Keynotes & Plenaries'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='TRAINING_WORKSHOP')
    tag.title = 'Training Workshops'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='INSTITUTE')
    tag.title = 'Institutes'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='MOBILE_WORKSHOP')
    tag.title = 'Mobile Workshops'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='ORIENTATION_TOUR')
    tag.title = 'Orientiation Tours'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='SPECIAL_EVENT')
    tag.title = 'Special Events'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='MEETING')
    tag.title = 'Meetings'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='RECEPTION')
    tag.title = 'Receptions'
    tag.save()
    
    tag_type, created = TagType.objects.get_or_create(code='EVENTS_NATIONAL_AUDIENCE')
    tag_type.title = 'Conference: Audience'
    tag_type.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='MASTER_SERIES')
    tag.title = 'Master Series'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='EMERGING')
    tag.title = 'Emerging Professionals'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='COMMISSIONERS')
    tag.title = 'Planning Commissioners'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='CAREER')
    tag.title = 'Career Development'
    tag.save()
    
    tag_type, created = TagType.objects.get_or_create(code='DIVISION')
    tag_type.title = 'Division'
    tag_type.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='CITY')
    tag.title = 'City Planning and Management'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='COUNTY')
    tag.title = 'County Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='ECONOMIC')
    tag.title = 'Economic Development'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='ENVIRONMENT')
    tag.title = 'Environment, Natural Resources, and Energy'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='FEDERAL')
    tag.title = 'Federal Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='GALIP')
    tag.title = 'Gays & Lesbians in Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='HOUSING')
    tag.title = 'Housing and Community Development'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='INDIGENOUS')
    tag.title = 'Indigenous Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='INTERNATIONAL')
    tag.title = 'International'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='LATINO')
    tag.title = 'Latinos and Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='NEW_URBANISM')
    tag.title = 'New Urbanism Division'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='LAW')
    tag.title = 'Planning and Law'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='BLACK_COMMUNITY')
    tag.title = 'Planning and the Black Community'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='WOMEN')
    tag.title = 'Planning and Women'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='PRIVATE')
    tag.title = 'Private Practice'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='REGIONAL')
    tag.title = 'Regional and Intergovernmental Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='SMALL_TOWN')
    tag.title = 'Small Town and Rural Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='SUSTAINABLE')
    tag.title = 'Sustainable Communities'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='TECHNOLOGY')
    tag.title = 'Technology Division'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='TRANSPORTATION')
    tag.title = 'Transportation Planning'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='URBAN_DESIGN')
    tag.title = 'Urban Design and Preservation'
    tag.save()
    
 
    tag_type, created = TagType.objects.get_or_create(code='EVENTS_NATIONAL_TRACK')
    tag_type.title = 'Conference: Tracks and Symposia'
    tag_type.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='SMART_CITIES')
    tag.title = 'Smart Cities and Sustainability Track'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='PARKS')
    tag.title = 'Parks, Recreation, and Greening Communities Track'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='OFFICE')
    tag.title = 'The Planning Office of the Future Track'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='NEW_ECONOMY')
    tag.title = 'The New Economy Track'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='WHOLE_STREETS')
    tag.title = 'Whole Streets Track'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='CLIMATE_CHANGE')
    tag.title = 'Planning and Climate Change Symposium'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='BOOMERS')
    tag.title = 'Millennials, Gen X, and Active Boomers Symposium'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='BETTMAN')
    tag.title = 'Bettman Symposium'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='ETHICS')
    tag.title = 'Israel Stollman Ethics Symposium'
    tag.save()
    
    tag_type, created = TagType.objects.get_or_create(code='EVENTS_NATIONAL_CEU')
    tag_type.title = 'Conference: CEU Credits'
    tag_type.save()

    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='AIA_LU')
    tag.title = 'AIA - LU'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='AIA_LU_HSW')
    tag.title = 'AIA - LU/HSW'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='AIA_LU_HSW_SD')
    tag.title = 'AIA - LU/HSW/SD'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='LA_CES_PDH')
    tag.title = 'LA CES - PDH'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='LA_CES_PDH_HSW')
    tag.title = 'LA CES - PDH/HSW'
    tag.save()
    
    tag, created = Tag.objects.get_or_create(tag_type=tag_type, code='MCLE_CLE')
    tag.title = 'MCLE - CLE'
    tag.save()