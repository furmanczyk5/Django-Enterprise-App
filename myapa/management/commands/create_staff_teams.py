from django.core.management.base import BaseCommand

from myapa.models.contact import Contact


wt_admin_list = [
            ('123377', 'Mike Welch'),
            ('317273', 'Renee Kronon-Schertz'),
            ('388715', 'Samantha Morse'),
        ]

class Command(BaseCommand):
    help = """Migrate the existing permission_groups.json group and user definitions
    to the new staff_teams field on the Contact model"""

    def add_staff_team(self, name, current_list, wagtail=False):
        if wagtail:
            current_list+=wt_admin_list
        for member_id in [x[0] for x in current_list]:
            try:
                contact = Contact.objects.get(user__username=member_id)
            except Contact.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        "No Contact found for ID {}".format(member_id)
                    )
                )
                continue
            if contact.staff_teams is None or not contact.staff_teams.strip():
                self.stdout.write(
                    self.style.NOTICE(
                        "Adding {} to the {} staff team".format(
                            contact,
                            name
                        )
                    )
                )
                contact.staff_teams = name
                contact.save()
            else:
                existing_staff_teams = contact.staff_teams.split(',')
                if name not in existing_staff_teams:
                    self.stdout.write(
                        self.style.NOTICE(
                            "Adding {} to the {} staff team".format(
                                contact,
                                name
                            )
                        )
                    )
                    existing_staff_teams.append(name)
                    existing_staff_teams.sort()
                    contact.staff_teams = ','.join(existing_staff_teams)
                    contact.save()

    def temp_staff(self):
        current_list = [
            ('278679', 'Sara Friedl-Putnam'),
            ('391411', 'Rachel Minion'),  # Mktg Contractor
            ('391410', 'Erin Eskildsen')  # Mktg Contractor
        ]

        self.add_staff_team('TEMP_STAFF', current_list)

    def conference_onsite(self):
        current_list = [
            ('339930', 'NPC REG'),
        ]
        self.add_staff_team('CONFERENCE_ONSITE', current_list)

    def staff_reviewer(self):
        current_list = [
            ('042872', 'Tom Lemon'),
            ('089655', 'David McInerney'),
            ('216879', 'Anna Read'),
            ('269926', 'Jen Graeff'),
        ]
        self.add_staff_team('STAFF_REVIEWER', current_list)

    def staff_editors(self):
        current_list = [
            ('119585', 'Cynthia Cheski'),
            ('081605', 'Ralph Jassen'),
            ('165605', 'Michael Johnson'),
            ('288069', 'Kelly Wilson'),
            ('162584', 'Julie Von Bergen')
        ]

        self.add_staff_team('EDITOR', current_list)

    def staff_store_admin(self):
        current_list = [
            ('322392', 'Bobbie Albrecht'),
            ('119585', 'Cynthia Cheski'),
            ('275324', 'Joseph DeAngelis'),
            ('181410', 'Ann Dillemuth'),
            ('259188', 'William French'),
            ('309833', 'Kathleen Gems'),
            ('081605', 'Ralph Jassen'),
            ('335276', 'Araceli Jimenez'),
            ('309810', 'Petra Hurtado'),
            ('284708', 'Milagros Marrero'),
            ('355413', 'Bekki Missaggia'),
            ('228137', 'Alisa Moore'),
            ('183154', 'David Morley'),
            ('368393', 'Alicia Navarro'),
            ('310352', 'Emily Pasi'),
            ('306990', 'Johamary Pena'),
            ('317273', 'Renee Kronon-Schertz'),
            ('232910', 'Jennifer Rolla'),
            ('268322', 'Karl Schmidt'),
            ('247903', 'Sagar Shah'),
            ('390825', 'Karen Allison'),
            ('288069', 'Kelly Wilson'),
            ('126862', 'Carlos Parra'),
            ('360649', 'Rachel Hoffman'),
            ('361287', 'Ryan Zack'),
            ('375048', 'Krystal White')
        ]

        self.add_staff_team('STORE_ADMIN', current_list)

    def staff_aicp(self):
        current_list = [
            ('274131', 'Felicia Braunstein'),
            ('181410', 'Ann Dillemuth'),
            ('259188', 'William French'),
            ('228137', 'Alisa Moore'),
            ('317273', 'Renee Kronon-Schertz'),
            ('362791', 'Yaminah Noonoo'),
            ('232910', 'Jennifer Rolla'),
            ('218838', 'Ryan Scherzinger'),
            ('361287', 'Ryan Zack'),
            ('375048', 'Krystal White')
        ]

        self.add_staff_team('AICP', current_list)

    def staff_marketing(self):
        current_list = [
            ('141400', 'Karen Kazmierczak'),
            ('283811', 'Elizabeth Lang'),
            ('344730', 'Molly Walsh'),
            ('119464', 'Susan Deegan'),
            ('391411', 'Rachel Minion'),  # Contractor
            ('391410', 'Erin Eskildsen')  # Contractor

        ]

        self.add_staff_team('MARKETING', current_list)

    def staff_membership(self):
        current_list = [
            ('362475', 'Brenna Donegan'),
            ('259188', 'William French'),
            ('309833', 'Kathleen Gems'),
            ('360649', 'Rachel Hoffman'),
            ('284708', 'Milagros Marrero'),
            ('126862', 'Carlos Parra'),
            ('268322', 'Karl Schmidt'),
            ('361287', 'Ryan Zack'),
        ]

        self.add_staff_team('MEMBERSHIP', current_list)

    def staff_education(self):
        current_list = [
            ('333834', 'Kimberley Jacques'),
            ('355413', 'Bekki Missaggia '),
            ('335276', 'Araceli Jimenez'),
            ('309810', 'Petra Hurtado'),
            ('183154', 'David Morley'),
            ('344730', 'Molly Walsh')
        ]

        self.add_staff_team('EDUCATION', current_list)

    def staff_careers(self):
        current_list = [
            ('322392', 'Bobbie Albrecht'),
            ('141400', 'Karen Kazmierczak')
        ]

        self.add_staff_team('CAREERS', current_list)

    def staff_publications(self):
        current_list = [
            ('275324', 'Joseph DeAngelis'),
            ('181410', 'Ann Dillemuth'),
            ('367790', 'Alex Gomez'),
            ('299816', 'Mary Hammon'),
            ('309810', 'Petra Hurtado'),
            ('183154', 'David Morley'),
            ('334229', 'Lindsay Nieman'),
            ('306990', 'Johamary Pena'),
            ('368373', 'Zenaid Santos'),
            ('247903', 'Sagar Shah'),
            ('162597', 'Meghan Stromberg'),
            ('162584', 'Julie Von Bergen'),
            ('358441', 'Cynthia Currie')
        ]

        self.add_staff_team('PUBLICATIONS', current_list)

    def staff_research(self):
        current_list = [
            ('364955', 'Chelsie Coren'),
            ('275324', 'Joseph DeAngelis'),
            ('181410', 'Ann Dillemuth'),
            ('367790', 'Alex Gomez'),
            ('309810', 'Petra Hurtado'),
            ('183154', 'David Morley'),
            ('306990', 'Johamary Pena'),
            ('363740', 'Conner Rettig'),
            ('368373', 'Zenaid Santos'),
            ('247903', 'Sagar Shah'),
            ('377820', 'Evan Williamson'),
            ('365925', 'Cassie E. Pettit')

        ]

        self.add_staff_team('RESEARCH', current_list)

    def staff_communications(self):
        current_list = [
            ('316890', 'Harriet Bogdanowicz'),
            ('362475', 'Brenna Donegan'),
            ('165243', 'Roberta Rewers')
        ]

        self.add_staff_team('COMMUNICATIONS', current_list)

    def staff_conference(self):
        current_list = [
            ('390825', 'Karen Allison'),
            ('228137', 'Alisa Moore'),
            ('284708', 'Milagros Marrero'),
            ('346895', 'Eva Wilczek'),
            ('368393', 'Alicia Navarro'),
            ('335276', 'Araceli Jimenez'),
            ('322392', 'Bobbie Albrecht'),
            ('344730', 'Molly Walsh')
        ]

        self.add_staff_team('CONFERENCE', current_list)

    def staff_policy(self):
        current_list = [
            ('362475', 'Brenna Donegan'),
            ('140010', 'Jason Jordan'),
            ('310352', 'Emily Pasi'),
            ('165243', 'Roberta Rewers'),
            ('316890', 'Harriet Bogdanowicz'),
        ]

        self.add_staff_team('POLICY', current_list)

    def staff_leadership(self):
        current_list = [
            ('117086', 'Lynn Jorgenson'),
            ('317273', 'Renee Kronon-Schertz'),
            ('362791', 'Yaminah Noonoo'),
            ('123377', 'Mike Welch'),
            ('332580', 'Maggie Kraus')
        ]

        self.add_staff_team('LEADERSHIP', current_list)

    def staff_events_editor(self):
        current_list = [
            ("390825", "Karen Allison"),
            ("335276", "Araceli Jimenez"),
            ("284708", "Milagros Marrero"),
            ("355413", "Bekki Missaggia"),
            ("228137", "Alisa Moore"),
            ('368393', 'Alicia Navarro'),
            ("310352", "Emily Pasi"),





        ]
        self.add_staff_team("EVENTS_EDITOR", current_list)

    def component_admin(self):
        # Replaces the "organization-store-admin" group

        # current_list = [(x.username, '') for x in Group.objects.get(
        #     name='organization-store-admin'
        # ).user_set.all()]

        # TODO: There are probably too many people in this group who shouldn't be
        # need to figure out who stays and who goes
        # Using the values in the old JSON file for now
        current_list = [
            ('088222', 'Shelia Booth'),
            ('108058', 'Christopher Shires'),
            ('217133', 'Madeline Sturms'),
            ('090421', 'Naomi Hamlett'),
            ('000480', 'Roger Bardsley'),
            ('157981', 'Angela Fuss'),
            ('151772', 'Erik Enyart'),
            ('198868', 'Chad Bunger'),
            ('291324', 'Francine Farrell'),
            ('268361', 'Benjamin Requet'),
        ]
        self.add_staff_team("COMPONENT_ADMIN", current_list)


    def black_admin(self):
        current_list = [
            ('330510', 'Dominique Edwards'),
            ('332644', 'Tatiana Height'),
            ('344048', 'Kayla Hunter'),
            ('068978', 'Victoria Mason-Ailey'),
            ('258474', 'Franchesca Taylor'),
            ('334606', 'Chanel Williams'),
            ('123377', 'Mike Welch'),
        ]
        self.add_staff_team('COMPONENT_BLACK', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def city_admin(self):
        current_list = []

        self.add_staff_team('COMPONENT_CITY', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def county_admin(self):
        current_list = [
            ('271198', 'David Heinold'),
            ('074143', 'Chris OKeefe'),
            ('152567', 'Jacqui Kamp'),
            ('199418', 'Kyle Breuer'),
        ]

        self.add_staff_team('COMPONENT_COUNTY', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def federal_admin(self):
        current_list = [
            ('316488', 'Heather Mendenall'),
            ('275358', 'Abbey Ness'),
            ('371050', 'Joshua Copeland'),
            ('162500', 'Andrew Wright')
        ]

        self.add_staff_team('COMPONENT_FEDERAL', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)


    def econ_admin(self):
        current_list = []

        self.add_staff_team('COMPONENT_ECON', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def env_admin(self):
        current_list = [
            ('264992', 'Jessica Conquest'),
            ('317999', 'Unai Miguel Andres'),
            ('274593', 'Aldo Treville'),
            ('171863', 'James Riordan'),
            ('132088', 'Sean Maguire '),
            ('072821', 'Vicki Oppenheim '),
        ]

        self.add_staff_team('COMPONENT_ENVIRON', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def hmdr_admin(self):
        current_list = [
            ('356694', 'Mikaela Sparks'),
            ('045343', 'Laura Bachle'),
            ('255555', 'Christine Caggiano')
        ]

        self.add_staff_team('COMPONENT_HMDR', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def housing_admin(self):
        current_list = [
            ('115198', 'Angela Brooks'),
            ('344264', 'Matthew Frater'),
            ('373805', 'Kanika Khanna'),
            ('348900', 'Brian Loughlin'),
            ('234991', 'Adam Perkins'),
            ('102011', 'Angela Self'),
            ('366725', 'Juan Sorto'),
        ]
        self.add_staff_team('COMPONENT_HOUSING', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def intl_admin(self):
        current_list = [
            ('216835', 'Michael Kolber'),
            ('305527', 'Sean Tapia'),
            ('258499', 'Jing Zhang'),
        ]

        self.add_staff_team('COMPONENT_INTL', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def lgbtq_admin(self):
        current_list = [
            ('086806', 'Tracey Corbitt'),
            ('159324', 'Justin Dula'),
            ('286128', 'Marcia J. Tobin')
        ]

        self.add_staff_team('COMPONENT_LGBTQ', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def private_admin(self):
        current_list = []

        self.add_staff_team('COMPONENT_PRIVATE', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def sustainable_admin(self):
        current_list = [
            ('172649', 'Matt Bucchin'),
            ('107980', 'Teresa Townsend'),
            ('272072', 'Jenny Koch'),
            ('315184', 'Fiona Coughlan'),
            ]

        self.add_staff_team('COMPONENT_SUSTAIN', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def tech_admin(self):
        current_list = [
            ('125237', 'Tom Coleman'),
            ('332461', 'Rebecca Nathanson'),
            ('119903', 'Tom Sanchez '),
            ('369329', 'Gerald Gordner'),
            ('262399', 'David Wasserman'),
            ('136079', 'Bev Wilson'),
            ]

        self.add_staff_team('COMPONENT_TECH', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def trans_admin(self):
        current_list = [
            ('181523', 'Lauren Good'),
            ('280125', 'Edson Ibanez'),
            ('295679', 'Mackenzie Jarvis'),
            ('161929', 'Gabriela Juarez'),
            ('305040', 'Lance MacNiven'),
            ('278578', 'Robert McHaney'),
            ('163257', 'Madhu Narayanasamy'),
            ('134181', 'Shelby Powell'),
            ('253478', 'Jamie Simchik'),
        ]

        self.add_staff_team('COMPONENT_TRANS', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def urban_des_admin(self):
        current_list = [
            ('274975', 'Brandon Robinson'),
            ('138199', 'Brian Foote')
        ]

        self.add_staff_team('COMPONENT_URBAN_DES', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def women_admin(self):
        current_list = [
            ('182843', 'Corrin Hoegen Wendell'),
            ('282688', 'Caroline Dwyer'),
            ('199186', 'Melissa Dickens'),
            ('334796', 'Katherine Jardieu'),
        ]
        self.add_staff_team('COMPONENT_WOMEN', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)


    def chapt_az_admin(self):
        current_list = [
            ('350938', 'Jessica Higley'),
            ('076877', 'Patti King'),
            ('359190', 'Viviane Walentiny'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_AZ', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_ca_admin(self):
        current_list = [
            ('281047', 'Gabriel Barreras'),
            ('291324', 'Francine Farrell'),
            ('222680', 'Laura Murphy'),
            ('214628', 'Marc Yeber'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_CA', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_co_admin(self):
        current_list = [
            ('088222', 'Shelia Booth'),
            ('135396', 'Scott Bressler'),
            ('199078', 'Sarah Davis'),
            ('343512', 'Joe Green'),
            ('245892', 'Shaida Libhart'),
            ('329365', 'Hadley Peterson'),
            ('138297', 'Michelle Stephens'),
            ('235000', 'Nick Vander Kwaak'),





        ]
        self.add_staff_team('COMPONENT_CHAPT_CO', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_ct_admin(self):
        current_list = [
            ('151451', 'Rebecca Augur'),
            ('141021', 'John Guszkowski'),
            ('206709', 'Amanda Kennedy'),
            ('291511', 'Carly Myers'),
            ('088112', 'Michael Piscitelli'),
            ('289984', 'Abigail St. Peter Kenyon'),
            ('011776', 'Alan Weiner'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_CT', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_fl_admin(self):
        current_list = [
            ('330062', 'Sean Baraoidan'),
            ('112000', 'Chuck Barmby, AICP'),
            ('137344', 'Marisa Barmby'),
            ('117757', 'Beth Beam'),
            ('239698', 'Aubyn Bell'),
            ('359887', 'Patricia Behn'),
            ('304063', 'Kori Benton'),
            ('096770', 'Wiatt Bowers, AICP'),
            ('355773', 'Juan Castillo'),
            ('280002', 'Craig Chandler'),
            ('017663', 'Terry Clark'),
            ('364486', 'Anthony Colao'),
            ('317871', 'Katrina Corcoran'),
            ('099902', 'Susan Coughanour'),
            ('247170', 'Matt Coyle'),
            ('315246', 'Joe Crozier'),
            ('133554', 'Brad Currie'),
            ('138917', 'Cayce Dagenhart'),
            ('213308', 'Christine Dalton'),
            ('113950', 'Alex Dambach'),
            ('268103', 'Ennis Davis'),
            ('088217', 'Alyce Decker, AICP'),
            ('124276', 'Gerry Dedenbach'),
            ('185569', 'Joshua DeVries'),
            ('199186', 'Melissa Dickens'),
            ('111176', 'Michael Disher'),
            ('257609', 'Elizabeth Eassa'),
            ('341797', 'Amy Elmore'),
            ('040396', 'Mike Escalante'),
            ('041240', 'Janis Fleet, AICP'),
            ('293336', 'Macy Fricke'),
            ('300349', 'Sofia Garantiva'),
            ('165653', 'Jacqueline Genson'),
            ('141163', 'Jason Green'),
            ('340042', 'Bethany Grubbs'),
            ('293131', 'Emily Hanna'),
            ('240123', 'Laurel Harbin'),
            ('063192', 'Hetty Harmon, AICP'),
            ('341942', 'Laura Herrscher, AICP'),
            ('004867', 'Carl Hintz'),
            ('310378', 'Leny Huaman'),
            ('329588', 'Daniel Hubbard'),
            ('214423', 'Angeline Jacobs'),
            ('343883', 'Brandon Johnson'),
            ('300798', 'Daniel Keester OMills'),
            ('332652', 'Eric Ketterling'),
            ('161489', 'Katie LaBarr'),
            ('335526', 'Jessica Leatherman'),
            ('247196', 'Devan Leavins'),
            ('305599', 'Elizabeth Levesque'),
            ('211833', 'Lindsay Libes'),
            ('215676', 'Van Linkous'),
            ('343170', 'Connor MacDonald'),
            ('049086', 'Julia Magee'),
            ('279732', 'Jennifer Malone'),
            ('066954', 'Marilyn Mammano'),
            ('220144', 'Stefanie McQueen'),
            ('196468', 'Leslie McLendon'),
            ('110142', 'Roger Menendez'),
            ('273594', 'Robert Modys'),
            ('353341', 'Alyssa Mohaghan'),
            ('248674', 'Eddie Ng '),
            ('143842', 'Luis Nieves - Ruiz '),
            ('203469', 'Stephen Noto'),
            ('145076', 'Kristen Nowicki'),
            ('329589', 'Dara Osher'),
            ('333098', 'Ali Palmer'),
            ('198620', 'Lucia Panica'),
            ('330918', 'Andrea Papandrew'),
            ('315670', 'Alicia Parinello'),
            ('183826', 'Brad Parrish'),
            ('357947', 'Lian Plass'),
            ('369078', 'Kylie Pope'),
            ('101938', 'Susan Poplin'),
            ('327675', 'Carmen Rasnick'),
            ('231079', 'Arceli Redila'),
            ('313380', 'Isabella Remolina'),
            ('303315', 'Lindsay Robin'),
            ('126023', 'Troy Salisbury'),
            ('119339', 'Martin Schneider'),
            ('258127', 'Josette Severyn'),
            ('346346', 'Katie Shannon'),
            ('354680', 'Patti Shea'),
            ('113514', 'Kristen Shell'),
            ('304559', 'Lindsay Slautterback'),
            ('165215', 'Nakeischea Smith'),
            ('070260', 'Ray Spofford, AICP'),
            ('188274', 'Irene Szedlmayer'),
            ('023455', 'Karen Taulbee, AICP'),
            ('214839', 'Ryan Thompson'),
            ('019363', 'Steve Tocknell, AICP'),
            ('279743', 'Nick Torres'),
            ('203422', 'Sue Trone, AICP'),
            ('223154', 'Jennifer Vail'),
            ('233135', 'Amanda Vickers'),
            ('068041', 'Tammy Vrana'),
            ('340424', 'Melissa Ward'),
            ('316301', 'Abigail Weiss'),
            ('321944', 'Rich Wilson'),
            ('105124', 'Tom Wodrich, AICP '),
            ('086483', 'Randy Woodruff, AICP'),
            ('340215', 'Tyler Woolsey'),
            ('303905', 'Lauren Yeatter'),
            ('135116', 'Ephrat Yovel'),
            ('352463', 'Camila Zablah Jimenez')
        ]

        self.add_staff_team('COMPONENT_CHAPT_FL', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_hi_admin(self):
        current_list = [
            ('302903', 'Erin Higa'),
            ('129045', 'Dean Minakami'),
            ('311778', 'Greg Nakai'),
            ('296317', 'Matthew Hom'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_HI', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_ia_admin(self):
        current_list = [
            ('380929', 'Andre Lafontant'),
            ('183959', 'Dylan Mullenix'),
            ('217133', 'Madeline Sturms'),
            ('198852', 'Tony Filippini'),
            ('199523', 'Bill Micheel'),
            ('109851', 'Seana Perkins'),
            ('299782', 'Liesl Seabert'),

        ]
        self.add_staff_team('COMPONENT_CHAPT_IA', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_in_admin(self):
        current_list = [
            ('302661', 'Jill Ewing'),
            ('096614', 'Bob Grewe'),
            ('386929', 'Kim Williams')
        ]
        self.add_staff_team('COMPONENT_CHAPT_IN', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_ks_admin(self):
        current_list = [
            ('198868', 'Chad Bunger'),
            ('236140', 'Joshua White'),
            ('152576', 'Erin Ollig'),
            ('217160', 'Stephanie Peterson'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_KS', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_mn_admin(self):
        current_list = [
            ('231626', 'Tim Gladhill'),
            ('123784', 'Haila Maze'),
            ('388817','Andrea Jauli'),
        ]

        self.add_staff_team('COMPONENT_CHAPT_MN', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_mo_admin(self):
        current_list = [
            ('331696', 'Megan Clark'),
            ('248942', 'John C Cruz'),
            ('310034', 'Wesley Haid'),
            ('142646', 'Susan Herre'),
            ('115251', 'Hilary Perkins'),
            ('234455', 'Bryan Ray'),
            ('305522', 'Lauren Reiman'),
            ('116824', 'Andrea Riganti'),
            ('300846', 'Jonathan Roper'),
            ('281263', 'Jessica Schuller'),
            ('359866', 'Aishwarya Shrestha'),
            ('282523', 'Jacob Trimble'),
        ]

        self.add_staff_team('COMPONENT_CHAPT_MO', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_nc_admin(self):
        current_list = [
            ('256658', 'Kara Louise'),
            ('104329', 'Paul Black'),
        ]
        self.add_staff_team('COMPONENT_CHAPT_NC', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_ncac_admin(self):
        current_list = [
            ('281986', 'Kayla Anthony'),
            ('181666', 'Clark Larson'),
            ('053526', 'Paul Moyer'),
            ('290842', 'Erkin Ozberk'),
            ('248189', 'Laura Searfoss'),
            ('177010', 'Lindsay Smith')
        ]
        self.add_staff_team('COMPONENT_CHAPT_NCAC', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)



    def chapt_ne_admin(self):
        current_list = [
            ('224687', 'Stacey Hageman'),
            ('270823', 'Stephanie Rouse'),
            ('080650', 'Bruce Fountain')
        ]
        self.add_staff_team('COMPONENT_CHAPT_NE', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_nne_admin(self):
        current_list = [
            ('150837', 'Tara Bamford'),
            ('304571', 'Donna Benton'),
            ('264830', 'Mark Connors'),
            ('125876', 'Kerrie Diers'),
            ('104563', 'Benjamin Frost'),
            ('365086', 'Nancy Gilbride'),
            ('131627', 'Sarah Hadd'),
            ('268391', 'Caitlyn Horose'),
            ('104002', 'Jeff Levine'),
            ('186013', 'Sarah Marchant'),
            ('303324', 'Heather Shank'),
            ('264860', 'Meagn Tuttle'),
            ('104691', 'Sue Westa')
        ]
        self.add_staff_team('COMPONENT_CHAPT_NNE', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_nv_admin(self):
        current_list = [
            ('303157', 'Amber Harmon'),
            ('281575', 'Lorenzo Mastino'),
            ('343041', 'Ellie Reeder'),
            ('337613', 'Erin Schwab'),
            ('344790', 'Annamarie Smith'),
            ('201294', 'Jared Tasko'),
            ('120041', 'Greg Toth'),
            ('057988', 'Garrett TerBerg III'),
            ('210601', 'Marco Velotta')
        ]
        self.add_staff_team('COMPONENT_CHAPT_NV', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_or_admin(self):
        current_list = [
            ('122631', 'Stephanie Kennedy'),
            ('122506', 'Susan Millhauser'),
            ('252999', 'Aaron Ray'),
            ('322605', 'Josh Williams')
        ]
        self.add_staff_team('COMPONENT_CHAPT_OR', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_tn_admin(self):
        current_list = [
            ('126477', 'Douglas Demosi'),
            ('310015', 'Troy Ebbert'),
            ('101842', 'Lynn Tully'),
            ('245445', 'Jessica Harmon'),
            ('345991', 'Cameron Taylor')
        ]

        self.add_staff_team('COMPONENT_CHAPT_TN', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_tx_admin(self):
        current_list = [
            ('354556', 'Hillary Bueker'),
            ('270523', 'Louis Cutaia'),
            ('357922', 'Jerald Ducay'),
            ('207628', 'AJ Fawver'),
            ('331368', 'Raul Garcia'),
            ('344275', 'Marco Hinojosa'),
            ('268561', 'Michael Howell'),
            ('337048', 'Allison Kay'),
            ('284101', 'Kyle Kingma'),
            ('007177', 'Michael McAnelly'),
            ('191483', 'Doug McDonald'),
            ('183387', 'Heather Nick'),
            ('219377', 'Abra Nusser'),
            ('201855', 'Rebecca Pacini'),
            ('269596', 'Michelle Queen'),
            ('224718', 'Christina Sebastian'),
            ('145068', 'Chance Sparks'),
            ('308937', 'Eleana Tuley'),
            ('353291', 'Macie Wyers'),
            ('357623', 'Glenda ArroyoCruz'),
            ('125496', 'Shai Roos')
             ]

        self.add_staff_team('COMPONENT_CHAPT_TX', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_va_admin(self):
        current_list = [
            ('049558', 'George Homewood'),
            ('198502', 'Andrew Hopewell'),
            ('069854', 'Eldon James'),
            ('120847', 'Earl Anderson'),
            ('164572', 'Jason Epsie'),
            ('224757', 'John Harbin'),
            ('233281', 'Brandie Schaeffer'),
            ('273955', 'Mark Klein'),
            ('284564', 'James May'),
            ('314580', 'Whitney Sokolowski'),
            ('338468', 'Sarah Pentecost'),
            ('329533', 'Caitlin Yates')
        ]

        self.add_staff_team('COMPONENT_CHAPT_VA', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_wcc_admin(self):
        current_list = [
            ('064720', 'Jeff Bollman'),
            ('339325', 'Jacob Cote'),
            ('271198', 'David Heinold'),
            ('303797', 'Kevin Hoekman'),
            ('072877', 'W. Randall Johnson'),
            ('176965', 'Megan Nelms'),
        ]

        self.add_staff_team('COMPONENT_CHAPT_WCC', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)

    def chapt_wi_admin(self):
        current_list = [
            ('103206', 'Nancy Frank'),
            ('332763', 'Cassandra Leopold'),
            ('356555', 'Forrest Elliot'),
            ('365738', 'Cody Garcia'),
        ]

        self.add_staff_team('COMPONENT_CHAPT_WI', current_list, wagtail=True)
        self.add_staff_team("JOBS_ADMIN", current_list)



    def handle(self, *args, **options):
        self.temp_staff()
        self.staff_editors()
        self.staff_aicp()
        self.staff_marketing()
        self.staff_membership()
        self.staff_education()
        self.staff_careers()
        self.staff_publications()
        self.staff_communications()
        self.staff_research()
        self.staff_conference()
        self.staff_policy()
        self.staff_leadership()
        self.conference_onsite()
        self.staff_reviewer()
        self.staff_store_admin()
        self.staff_events_editor()
        self.component_admin()
        self.black_admin()
        self.city_admin()
        self.county_admin()
        self.federal_admin()
        self.econ_admin()
        self.env_admin()
        self.hmdr_admin()
        self.housing_admin()
        self.intl_admin()
        self.lgbtq_admin()
        self.private_admin()
        self.sustainable_admin()
        self.tech_admin()
        self.trans_admin()
        self.urban_des_admin()
        self.women_admin()
        self.chapt_az_admin()
        self.chapt_ca_admin()
        self.chapt_co_admin()
        self.chapt_ct_admin()
        self.chapt_fl_admin()
        self.chapt_hi_admin()
        self.chapt_ia_admin()
        self.chapt_in_admin()
        self.chapt_ks_admin()
        self.chapt_mn_admin()
        self.chapt_mo_admin()
        self.chapt_nc_admin()
        self.chapt_ncac_admin()
        self.chapt_ne_admin()
        self.chapt_nne_admin()
        self.chapt_nv_admin()
        self.chapt_or_admin()
        self.chapt_tn_admin()
        self.chapt_tx_admin()
        self.chapt_va_admin()
        self.chapt_wcc_admin()
        self.chapt_wi_admin()
