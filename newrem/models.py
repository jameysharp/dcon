from datetime import datetime

from flaskext.sqlalchemy import SQLAlchemy

from newrem.main import app

db = SQLAlchemy(app)

casts = db.Table("casts", db.metadata,
    db.Column("character_id", db.String, db.ForeignKey("characters.slug")),
    db.Column("comic_id", db.Integer, db.ForeignKey("comics.id"))
)

class Character(db.Model):
    """
    A character.
    """

    __tablename__ = "characters"

    name = db.Column(db.String)
    slug = db.Column(db.String, primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Character(%r)>" % self.name

    def rename(self, name):
        self.name = name
        self.slug = name.strip().lower().replace(" ", "-")

class Comic(db.Model):
    """
    A comic.
    """

    __tablename__ = "comics"

    # Serial number, for simple PK.
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    # Upload time.
    time = db.Column(db.DateTime, unique=True, nullable=False)
    # Local filename.
    filename = db.Column(db.String, unique=True, nullable=False)
    # Position in the timeline.
    position = db.Column(db.Integer, nullable=False)

    # List of characters in this comic.
    characters = db.relationship("Character", secondary=casts,
        backref="comics")

    def __init__(self, filename):
        self.filename = filename
        self.time = datetime.utcnow()

    def __repr__(self):
        return "<Comic(%r)>" % self.filename

    @classmethod
    def reorder(cls):
        """
        Compact chronological ordering.

        The reason for doing this is almost completely aesthetic.
        """

        for i, comic in enumerate(cls.query.order_by(cls.position)):
            if comic.position != i:
                comic.position = i
                db.session.add(comic)

    def insert_at_head(self):
        """
        Make this comic the very first comic.
        """

        self.position = 0
        db.session.add(self)

        q = Comic.query.filter(Comic.id != self.id)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + 1:
                comic.position = i + 1
                db.session.add(comic)

    def insert(self, prior):
        """
        Move this comic to come just after another comic in the timeline.
        """

        if not prior:
            # First insertion in the table, ever. Let's just set ourselves to
            # zero and walk away.
            self.position = 1
            db.session.add(self)
            return

        position = prior.position + 1

        q = Comic.query.filter(Comic.position >= position)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + position:
                comic.position = i + position
                db.session.add(comic)

        self.position = position
        db.session.add(self)
