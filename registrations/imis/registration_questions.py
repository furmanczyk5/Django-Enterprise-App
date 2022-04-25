from .db_accessor import DbAccessor

def get_questions(event_code):
    query = """
    SELECT * FROM vSoaEvent 
    INNER JOIN FormDefinitionField on vSoaEvent.FormDefinitionSectionKey = FormDefinitionField.FormDefinitionSectionKey 
    INNER JOIN FormDefinitionSection ON vSoaEvent.FormDefinitionSectionKey = FormDefinitionSection.FormDefinitionSectionKey 
    WHERE EventId=?
    """
    return serialize_questions(DbAccessor().get_rows(query, event_code))


def serialize_questions(rows):
    serialized_rows = {}
    for row in rows:
        serialized_rows[row.FormDefinitionFieldSequence] = {
            'field_key': row.FormDefinitionFieldKey,
            'section_key': row.FormDefinitionSectionKey,
            'form_key': row.FormDefinitionKey,
            'label': row.FormDefinitionFieldCaption,
            'xml': row.SerializedPropertyDefinition,
            'type': row.FormDefinitionFieldType
        }
    return serialized_rows


def create_response_key(form_key, user_id):
    query = """
        DECLARE @key VARCHAR(36)=?, @id VARCHAR(10)=?
        IF NOT EXISTS 
        (SELECT 1
        FROM FormResponse 
        WHERE FormDefinitionKey = @key
        AND ID = @id
        )
        BEGIN
        INSERT FormResponse (FormDefinitionKey, ID) 
        VALUES (@key, @id) 
        END;
        SELECT FormResponseKey FROM FormResponse
        WHERE ID = @id AND FormDefinitionKey = @key
        """
    return DbAccessor().get_row(query, [form_key, user_id]).FormResponseKey


def insert_response_value(response_key, field_key, response_type, response):
    types = {
        'Decimal': 'FieldDecimalValue',
        'DateTime': 'FieldDateTimeValue',
        'String': 'FieldStringValue',
        'Integer': 'FieldIntegerValue',
        'Boolean': 'FieldBooleanValue'
    }
    delete = """
        DELETE FROM FormResponseField
        WHERE FormResponseKey=? AND FormDefinitionFieldKey=?
    """
    replace = (
        'INSERT INTO FormResponseField '
        "(FormResponseKey, FormDefinitionFieldKey, {}) VALUES (?, ?, ?)"
    ).format(types[response_type])
    DbAccessor().execute(delete, [response_key, field_key])
    DbAccessor().execute(replace, [response_key, field_key, response])
