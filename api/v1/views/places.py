#!/usr/bin/python3
"""Places API."""

from flask import jsonify, request, abort
from models import storage
from models.city import City
from models.place import Place
from models.user import User
from api.v1.views import app_views


@app_views.route('/cities/<city_id>/places', methods=['GET', 'POST'])
@app_views.route('/places/<place_id>', methods=['GET', 'PUT', 'DELETE'])
def places(city_id=None, place_id=None):
    """Handles places operations."""
    if request.method == 'GET':
        return get_places(city_id, place_id)
    elif request.method == 'POST':
        return create_place(city_id)
    elif request.method == 'PUT':
        return update_place(place_id)
    elif request.method == 'DELETE':
        return delete_place(place_id)
    else:
        abort(405)


def get_places(city_id=None, place_id=None):
    """Retrieve places."""
    if city_id:
        city = storage.get(City, city_id)
        if not city:
            abort(404)
        places = [place.to_dict() for place in
                  storage.all(Place).values() if place.city_id == city_id]
        return jsonify(places)
    elif place_id:
        place = storage.get(Place, place_id)
        if not place:
            abort(404)
        return jsonify(place.to_dict())
    abort(404)


def create_place(city_id):
    """Create a new place."""
    city = storage.get(City, city_id)
    if not city:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, 'Not a JSON')
    if 'user_id' not in data:
        abort(400, 'Missing user_id')
    user = storage.get(User, data['user_id'])
    if not user:
        abort(404)
    if 'name' not in data:
        abort(400, 'Missing name')
    new_place = Place(name=data['name'], user_id=data['user_id'],
                      city_id=city_id)
    new_place.save()
    return jsonify(new_place.to_dict()), 201


def update_place(place_id):
    """Update a place."""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    data = request.get_json()
    if not data:
        abort(400, 'Not a JSON')
    ignore_keys = ('id', 'user_id', 'city_id', 'created_at', 'updated_at')
    for key, value in data.items():
        if key not in ignore_keys:
            setattr(place, key, value)
    place.save()
    return jsonify(place.to_dict()), 200


def delete_place(place_id):
    """Delete a place."""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)
    storage.delete(place)
    storage.save()
    return jsonify({}), 200
