#==========================================================================#
# IMPORTS
#==========================================================================#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#==========================================================================#
# APP CONFIG
#==========================================================================#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Set a variable that all routes can access.
current_time = datetime.utcnow()

#==========================================================================#
# MODELS
#==========================================================================#


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)


class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        "venues.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        "artists.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    venue = db.relationship("Venue", backref="shows", lazy="joined")
    artist = db.relationship("Artist", backref="shows", lazy="joined")

#==========================================================================#
# FILTERS
#==========================================================================#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE, MMMM d, y 'at' h:mma"
    elif format == "medium":
        format = "EE, MM dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters["datetime"] = format_datetime

#==========================================================================#
# CONTROLLERS
#==========================================================================#


@app.route("/")
def index():
    return render_template("pages/home.html")

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []

    locations = Venue.query.distinct(Venue.city, Venue.state)

    for location in locations:
        locations = Venue.query.filter_by(city=location.city).outerjoin(
            Show, Venue.id == Show.venue_id).all()

        venues = []
        for venue in locations:
            upcoming_shows = []
            shows = venue.shows
            for show in shows:
                if show.start_time > current_time:
                    upcoming_shows.append(show)

            venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows)
            })

        data.append({
            "city": location.city,
            "state": location.state,
            "venues": venues
        })

    return render_template("pages/venues.html", areas=data)

#  ----------------------------------------------------------------
#  Venues Search
#  ----------------------------------------------------------------


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search = request.form.get("search_term", "")
    venues = Venue.query.filter(Venue.name.ilike(f"%{search}%")).outerjoin(
        Show, Venue.id == Show.venue_id).all()
    data = []

    for venue in venues:
        upcoming_shows = []
        shows = venue.shows
        for show in shows:
            if show.start_time > current_time:
                upcoming_shows.append(show)

        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(upcoming_shows)
        })

    response = {
        "count": len(venues),
        "data": data
    }

    return render_template("pages/search_venues.html", results=response, search_term=search)

#  ----------------------------------------------------------------
#  Venue
#  ----------------------------------------------------------------


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).outerjoin(
        Show, Venue.id == Show.venue_id).all()

    for venue in venue:
        shows = venue.shows
        past_shows = []
        upcoming_shows = []

        for show in shows:
            show_data = {
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            }

            if show.start_time < current_time:
                past_shows.append(show_data)
            else:
                upcoming_shows.append(show_data)

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
        }

    return render_template("pages/show_venue.html", venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    error = False
    try:
        name = request.form["name"]
        city = request.form["city"]
        state = request.form["state"]
        address = request.form["address"]
        phone = request.form["phone"]
        genres = request.form.getlist("genres")
        image_link = request.form["image_link"]
        facebook_link = request.form["facebook_link"]
        website = request.form["website"]
        if "seeking_talent" in request.form:
            seeking_talent = True
        else:
            seeking_talent = False
        seeking_description = request.form["seeking_description"]
        venue = Venue(name=name, city=city, state=state, address=address,
                      phone=phone, genres=genres, image_link=image_link, facebook_link=facebook_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
        db.session.add(venue)
        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully listed!")
    except Exception as e:
        print(e)
        db.session.rollback()
        error = True
        flash("Venue could not be saved.")
    finally:
        db.session.close()

    return render_template("pages/home.html")

#  ----------------------------------------------------------------
#  Edit Venue
#  ----------------------------------------------------------------


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue_data = Venue.query.get(venue_id)
    form = VenueForm(obj=venue_data)

    venue = {
        "id": venue_data.id,
        "name": venue_data.name,
        "address": venue_data.address,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "genres": venue_data.genres,
        "image_link": venue_data.image_link,
        "facebook_link": venue_data.facebook_link,
        "website": venue_data.website,
        "seeking_talent": venue_data.seeking_talent,
        "seeking_description": venue_data.seeking_description
    }

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    try:
        name = request.form["name"]
        city = request.form["city"]
        state = request.form["state"]
        address = request.form["address"]
        phone = request.form["phone"]
        genres = request.form.getlist("genres")
        image_link = request.form["image_link"]
        facebook_link = request.form["facebook_link"]
        website = request.form["website"]
        if "seeking_talent" in request.form:
            seeking_talent = True
        else:
            seeking_talent = False
        seeking_description = request.form["seeking_description"]
        venue = Venue.query.get(venue_id)
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.genres = genres
        venue.image_link = image_link
        venue.facebook_link = facebook_link
        venue.website = website
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully updated!")
    except Exception as e:
        print(e)
        db.session.rollback()
        error = True
        flash("Venue could not be updated.")
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))

#  ----------------------------------------------------------------
#  Delete Venue
#  ----------------------------------------------------------------


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue successfully deleted.")
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Venue could not be deleted.")
    finally:
        db.session.close()

    return render_template("pages/home.html")

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route("/artists")
def artists():
    artists = Artist.query.all()
    data = []

    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template("pages/artists.html", artists=data)

#  ----------------------------------------------------------------
#  Artists Search
#  ----------------------------------------------------------------


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike(f"%{search}%")).outerjoin(
        Show, Venue.id == Show.venue_id).all()
    data = []

    for artist in artists:
        shows = artist.shows
        upcoming_shows = []

        for show in shows:
            if show.start_time > current_time:
                upcoming_shows.append(show)

        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(upcoming_shows)
        })

    response = {
        "count": len(artists),
        "data": data
    }

    return render_template("pages/search_artists.html", results=response, search_term=search)

#  ----------------------------------------------------------------
#  Artist
#  ----------------------------------------------------------------


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).outerjoin(
        Show, Artist.id == Show.venue_id).all()

    for artist in artist:
        shows = artist.shows
        past_shows = []
        upcoming_shows = []

        for show in shows:
            show_data = {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": format_datetime(str(show.start_time))
            }
            if show.start_time < current_time:
                past_shows.append(show_data)
            else:
                upcoming_shows.append(show_data)

        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
        }

    return render_template("pages/show_artist.html", artist=data)

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    try:
        name = request.form["name"]
        city = request.form["city"]
        state = request.form["state"]
        phone = request.form["phone"]
        genres = request.form.getlist("genres")
        image_link = request.form["image_link"]
        facebook_link = request.form["facebook_link"]
        website = request.form["website"]
        if "seeking_venue" in request.form:
            seeking_venue = True
        else:
            seeking_venue = False
        seeking_description = request.form["seeking_description"]
        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, image_link=image_link,
                        facebook_link=facebook_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully listed!")
    except Exception as e:
        print(e)
        db.session.rollback()
        error = True
        flash("Artist could not be saved.")
    finally:
        db.session.close()

    return render_template("pages/home.html")

#  ----------------------------------------------------------------
#  Update Artist
#  ----------------------------------------------------------------


@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist_data = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist_data)
    artist = {
        "id": artist_data.id,
        "name": artist_data.name,
        "genres": artist_data.genres,
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": artist_data.phone,
        "website": artist_data.website,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link
    }

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    try:
        name = request.form["name"]
        city = request.form["city"]
        state = request.form["state"]
        phone = request.form["phone"]
        genres = request.form.getlist("genres")
        image_link = request.form["image_link"]
        facebook_link = request.form["facebook_link"]
        website = request.form["website"]
        if "seeking_venue" in request.form:
            seeking_venue = True
        else:
            seeking_venue = False
        seeking_description = request.form["seeking_description"]
        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, image_link=image_link,
                        facebook_link=facebook_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.genres = genres
        artist.image_link = image_link
        artist.facebook_link = facebook_link
        artist.website = website
        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully updated!")
    except Exception as e:
        print(e)
        db.session.rollback()
        error = True
        flash("Artist could not be updated.")
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))

#  ----------------------------------------------------------------
#  Delete Artist
#  ----------------------------------------------------------------


@app.route("/artists/<artist_id>", methods=["DELETE"])
def delete_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash("Artist successfully deleted.")
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Artist could not be deleted.")
    finally:
        db.session.close()

    return render_template("pages/home.html")

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    shows = Show.query.all()
    data = []

    for show in shows:
        show_data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        }

        data.append(show_data)

    return render_template("pages/shows.html", shows=data)

#  ----------------------------------------------------------------
#  Create Show
#  ----------------------------------------------------------------


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    error = False
    try:
        venue_id = request.form["venue_id"]
        artist_id = request.form["artist_id"]
        start_time = request.form["start_time"]
        show = Show(venue_id=venue_id, artist_id=artist_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("Show could not be listed.")
    finally:
        db.session.close()

    return render_template("pages/home.html")

#==========================================================================#
#  ERROR HANDLERS
#==========================================================================#


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

#==========================================================================#
# LAUNCH
#==========================================================================#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
'''
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
'''
