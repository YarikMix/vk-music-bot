from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker


maker = PetrovichDeclinationMaker()

def decline(first_name, last_name):
    """Возвращает имя и фамилию в родительном падаже."""
    first_name = maker.make(NamePart.FIRSTNAME, Gender.MALE, Case.GENITIVE, first_name)
    last_name = maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, last_name)
    return first_name + " " + last_name