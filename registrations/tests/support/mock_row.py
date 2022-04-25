class MockRow():
    ID = '67890'
    FIRST_NAME = 'Robert'
    LAST_NAME = 'Jenkins'
    INFORMAL = 'Bob'
    COMPANY = 'Acme'
    CITY = 'Phoenix'
    STATE_PROVINCE = 'AZ'
    ADDRESS_1 = '123 Lane'
    ADDRESS_2 = 'Apt 123'
    ZIP = '54321'

    def __init__(self, country='United States'):
        self.COUNTRY = country
