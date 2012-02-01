from werkzeug.routing import BaseConverter, ValidationError

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

class ModelConverter(BaseConverter):
    """
    Converts a URL segment to and from a SQLAlchemy model.

    Rather than use an initializer, this class should be subclassed and have
    the `model` and `field` class attributes filled in. `model` is the
    Flask-SQLAlchemy model to use for queries, and `field` is the field on the
    model to use for lookups.

    The field to use should be Unicode or bytes.
    """

    def to_python(self, value):
        try:
            with self.app.test_request_context():
                obj = self.model.query.filter_by(**{self.field: value}).one()
        except (MultipleResultsFound, NoResultFound):
            raise ValidationError()

        return obj

    def to_url(self, value):
        return getattr(value, self.field)

def make_model_converter(a, m, f):
    """
    Create a ModelConverter for the given app, model, and field.
    """

    class Subclass(ModelConverter):
        app = a
        field = f
        model = m

    return Subclass