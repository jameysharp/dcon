from werkzeug import secure_filename

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from flask.ext.wtf import FileRequired

from sqlalchemy.orm.exc import NoResultFound

from newrem.config import load_config, write_config
from newrem.files import save_file
from newrem.forms import (ConfigForm, CreateCharacterForm,
                          DeleteCharacterForm, ModifyCharacterForm, NewsForm,
                          EditNewsForm, CreatePortraitForm,
                          ModifyPortraitForm, CreateUniverseForm,
                          ModifyUniverseForm, DeleteUniverseForm,
                          CreateComicForm, ModifyComicForm)
from newrem.models import (db, Board, Character, Comic, Newspost, Portrait,
    Thread, Universe)
from newrem.security import Authenticator
from newrem.util import abbreviate


class AdminBlueprint(Blueprint):
    """
    Custom blueprint which automatically authenticates its views.
    """

    def register(self, app, options, first_registration=False):
        """
        Register this blueprint on an application.
        """

        fp = app.config["DCON_PASSWORD_FILE"]
        d = {}
        for line in fp.open("rb").read().split("\n"):
            try:
                k, v = line.split(":", 1)
            except ValueError:
                pass
            else:
                d[k.strip()] = v.strip()

        self._authenticator = Authenticator(d)

        self.before_request(lambda: self._require_authentication(app))

        Blueprint.register(self, app, options, first_registration)

    def _require_authentication(self, app):
        auth = request.authorization
        if not auth or not self._authenticator.validate(auth):
            return self._authenticator.make_basic_challenge("Cid's Lair",
                "Haha, no.")


admin = AdminBlueprint("admin", __name__, static_folder="static",
    template_folder="templates/admin")


@admin.route("/")
def index():
    form = CreateUniverseForm()
    universes = Universe.query.order_by(Universe.title)

    return render_template("admin.html", form=form, universes=universes)


@admin.route("/config")
def config():
    form = ConfigForm(current_app)
    return render_template("config.html", form=form)


@admin.route("/reload", methods=("POST",))
def config_reload():
    form = ConfigForm(current_app)

    if form.validate_on_submit():
        config = current_app.config["DCON_CONFIG"]
        config["upload_time_now"] = form.upload_time_now.data

        write_config(current_app)
        load_config(current_app)
        flash("Saved and reloaded site configuration!")

    return redirect(url_for("admin.config"))


@admin.route("/<universe:u>/")
def universe(u):
    form = ModifyUniverseForm()

    return render_template("admin-universe.html", form=form, u=u)

@admin.route("/universe/create", methods=("POST",))
def universe_create():
    form = CreateUniverseForm()

    if form.validate_on_submit():
        universe = Universe(form.name.data)
        universe.board = Board(abbreviate(universe.title), universe.title)
        db.session.add(universe)
        db.session.commit()

        flash("Successfully created the universe of %s!" % universe.title)
        return redirect(url_for("admin.universe", u=universe))
    else:
        flash("Couldn't validate form. How'd that happen?")
        return redirect(url_for("admin.index"))

@admin.route("/<universe:u>/modify", methods=("POST",))
def universe_modify(u):
    form = ModifyUniverseForm()

    if form.validate_on_submit():
        old = u.title
        u.rename(form.name.data)
        db.session.add(u)
        db.session.commit()
        flash("Successfully renamed the universe of %s to %s!" %
            (old, u.title))

    return redirect(url_for("admin.universe", u=u))

@admin.route("/<universe:u>/delete", methods=("GET", "POST"))
def universe_delete(u):
    form = DeleteUniverseForm()

    if form.validate_on_submit():
        if form.verify.data:
            db.session.delete(u)
            db.session.commit()
            flash("Successfully destroyed universe %s!" % u.title)
        else:
            flash("Guess you changed your mind, huh? No worries.")

        return redirect(url_for("admin.index"))
    else:
        return render_template("universe-delete.html", form=form, u=u)

@admin.route("/<universe:u>/characters")
def characters(u):
    q = Character.query.filter_by(universe=u).order_by(Character.name)
    characters = q.all()
    form = CreateCharacterForm()

    return render_template("characters.html", form=form, u=u,
        characters=characters)

@admin.route("/<universe:u>/characters/<character:c>")
def character(u, c):
    mform = ModifyCharacterForm(prefix="modify", name=c.name, major=c.major,
                                description=c.description)
    dform = DeleteCharacterForm(prefix="delete")

    # Character needs to be bound to a session.
    db.session.add(c)

    return render_template("character.html", mform=mform, dform=dform, u=u,
        c=c)

@admin.route("/<universe:u>/characters/create", methods=("POST",))
def characters_create(u):
    form = CreateCharacterForm()

    if form.validate_on_submit():
        character = Character(u, form.name.data)
        character.major = form.major.data
        if form.description.data:
            character.description = form.description.data
        db.session.add(character)
        db.session.commit()

        if form.portrait.file:
            save_file(character.fp(), form.portrait.file)

        flash("Successfully created character %s!" % character.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.characters", u=u))

@admin.route("/<universe:u>/characters/<character:c>/modify",
    methods=("POST",))
def characters_modify(u, c):
    form = ModifyCharacterForm(prefix="modify")

    if form.validate_on_submit():
        # Which modifications do we want to make?
        db.session.add(c)

        if form.name.data and form.name.data != c.name:
            c.rename(form.name.data)
            flash("Successfully renamed character %s!" % c.name)

        c.major = form.major.data

        if form.portrait.file:
            if save_file(c.fp(), form.portrait.file):
                flash("Successfully changed portrait for character %s!" %
                    c.name)
            else:
                flash("Couldn't save portrait for character %s..." % c.name)

        if form.description.data != c.description:
            if form.description.data:
                c.description = form.description.data
            else:
                c.description = None
            flash("Successfully changed description for character %s!" %
                c.name)

        db.session.commit()
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.character", u=u, c=c))

@admin.route("/<universe:u>/characters/<character:c>/delete",
    methods=("POST",))
def characters_delete(u, c):
    form = DeleteCharacterForm(prefix="delete")

    if form.validate_on_submit():
        db.session.delete(c)
        db.session.commit()
        c.fp().remove()
        flash("Successfully removed character %s!" % c.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.characters", u=u))

@admin.route("/portraits")
def portraits():
    cform = CreatePortraitForm(prefix="create")
    mform = ModifyPortraitForm(prefix="modify")

    return render_template("portraits.html", cform=cform, mform=mform)

@admin.route("/portraits/create", methods=("POST",))
def portraits_create():
    form = CreatePortraitForm(prefix="create")

    if form.validate_on_submit():
        portrait = Portrait(form.name.data)
        db.session.add(portrait)
        db.session.commit()

        portrait.update_portrait(form.portrait.file)

        flash("Successfully created portrait %s!" % portrait.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.portraits"))

@admin.route("/portraits/modify", methods=("POST",))
def portraits_modify():
    form = ModifyPortraitForm(prefix="modify")

    if form.validate_on_submit():
        portrait = form.portraits.data
        if portrait and form.portrait.file:
            portrait.update_portrait(form.portrait.file)

            flash("Successfully changed portrait for portrait %s!" %
                portrait.name)
        else:
            flash("Couldn't find portrait for slug %s..." %
                form.portraits.data)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.portraits"))

@admin.route("/news", methods=("GET", "POST"))
def news():
    form = NewsForm()

    if form.validate_on_submit():
        post = Newspost(form.title.data, form.content.data)
        post.portrait = form.portrait.data
        db.session.add(post)
        db.session.commit()
        flash("Successfully posted the news!")
        return redirect(url_for("index"))

    posts = Newspost.query.order_by(Newspost.time).all()
    return render_template("news.html", form=form, posts=posts)

@admin.route("/news/<newspost:n>", methods=("GET", "POST"))
def newsdetail(n):
    db.session.add(n)

    form = EditNewsForm()

    if form.validate_on_submit():
        n.time = form.time.data
        n.title = form.title.data
        n.content = form.content.data
        n.portrait = form.portrait.data
        db.session.add(n)
        db.session.commit()
        flash("Successfully edited the news!")
        return redirect(url_for("index"))

    form.time.data = n.time
    form.title.data = n.title
    form.content.data = n.content
    form.portrait.data = n.portrait
    return render_template("newsdetail.html", form=form, n=n)

@admin.route("/<universe:u>/comics", methods=("GET", "POST"))
def comics(u):
    q = Comic.query.filter_by(universe=u)
    comics = q.order_by(Comic.position)
    return render_template("admin-comics.html", u=u, comics=comics)


def find_reference(universe, index):
    """
    Look up the insertion comic and boolean for an index.
    """

    if index == -1:
        q = Comic.query.filter_by(universe=universe).order_by(Comic.position)
        reference = q.first()
        before = True
    else:
        reference = Comic.query.filter_by(universe=universe, id=index).one()
        before = False
    return reference, before


@admin.route("/<universe:u>/comics/create", methods=("GET", "POST"))
def comics_create(u):
    form = CreateComicForm(u)
    form.file.validators += (FileRequired("Must upload a comic!"),)

    if form.validate_on_submit():
        # Hold it! We need to check that the insert position is correct by
        # looking up the comic that we're gonna use for insert().
        if form.index.data != -2:
            try:
                reference, before = find_reference(u, form.index.data)
            except Exception, e:
                flash("Couldn't position comic: %s" % ", ".join(e.args))
                return render_template("upload.html", form=form, u=u)

        db.session.add(u)
        filename = secure_filename(form.file.file.filename)

        try:
            comic = Comic(u, filename)
        except Exception, e:
            flash("Couldn't create comic: %s" % ", ".join(e.args))
            return render_template("upload.html", form=form, u=u)

        comic.characters = form.characters.data
        comic.title = form.title.data
        comic.description = form.description.data
        comic.comment = form.comment.data
        comic.thread = Thread(u.board, comic.title, "DCoN")

        if form.time.data:
            comic.time = form.time.data

        if form.index.data != -2:
            comic.insert(reference, before)
        else:
            comic.position = 0

        db.session.add(comic)
        db.session.commit()

        save_file(comic.fp(), form.file.file)

        return redirect(url_for("admin.comics_modify", u=u, cid=comic.id))

    return render_template("upload.html", form=form, u=u)

@admin.route("/<universe:u>/comics/<int:cid>/modify", methods=("GET", "POST"))
def comics_modify(u, cid):
    try:
        comic = Comic.query.filter_by(id=cid).one()
    except NoResultFound:
        abort(404)

    form = ModifyComicForm(u)

    if form.validate_on_submit():
        db.session.add(u)

        # Attempt to set the new filename, and then verify it.
        if form.file.file:
            comic.filename = secure_filename(form.file.file.filename)
            try:
                comic.verify_fp()
            except Exception, e:
                flash("Couldn't alter comic: %s" % ", ".join(e.args))
                return render_template("upload-modify.html", form=form, u=u,
                                       comic=comic)

        comic.characters = form.characters.data
        comic.title = form.title.data
        comic.description = form.description.data
        comic.comment = form.comment.data

        if form.time.data:
            comic.time = form.time.data

        # Hold it! We need to check that the insert position is correct by
        # looking up the comic that we're gonna use for insert().
        if form.index.data != -2:
            try:
                reference, before = find_reference(u, form.index.data)
            except Exception, e:
                flash("Couldn't position comic: %s" % ", ".join(e.args))
                return render_template("upload-modify.html", form=form, u=u,
                                       comic=comic)

        if reference.id != comic.id and form.index.data != -2:
            comic.insert(reference, before)

        db.session.add(comic)
        db.session.commit()

        # Only write a new image down if requested.
        if form.file.file:
            save_file(comic.fp(), form.file.file)

        return render_template("upload-modify.html", form=form, u=u,
                               comic=comic)

    # Populate the form.
    form.characters.data = comic.characters
    form.title.data = comic.title
    form.description.data = comic.description
    form.comment.data = comic.comment
    form.time.data = comic.time
    form.index.data = comic.id

    return render_template("upload-modify.html", form=form, u=u, comic=comic)
