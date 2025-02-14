from itou.metabase.tables.utils import MetabaseTable, get_column_from_field
from itou.users.models import User


def get_field(name):
    return User._meta.get_field(name)


TABLE = MetabaseTable(name="utilisateurs")
TABLE.add_columns(
    [
        get_column_from_field(get_field("id"), name="id"),
        get_column_from_field(get_field("email"), name="email"),
        get_column_from_field(get_field("kind"), name="type"),
    ]
)
