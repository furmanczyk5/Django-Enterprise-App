from enum import Enum


class BlankEnum(Enum):

    BLANK = ''


def get_label_for_enum(enum_class, enum_value):
    """
    Get the label value for one of the enums defined in imis.enums
    :param enum_class: :class:`enum.Enum`
    :param enum_value: str, the enum attribute to get the value of
    :return: str
    """

    return getattr(
        enum_class,
        "{}_LABEL".format(enum_value),
        BlankEnum.BLANK
    ).value
