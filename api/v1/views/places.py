#!/usr/bin/python3
"""Places API."""

from flask import jsonify, request, abort
from models import storage, storage_t
from models.city import City
from models.place import Place
from models.user import User
from models.amenity import Amenity
from models.state import State
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


@app_views.route('/places_search', methods=['POST'])
def find_places():
    '''Finds places based on a list of State, City, or Amenity ids.
    '''
    data = request.get_json()
    if type(data) is not dict:
        abort(400, 'Not a JSON')
    all_places = storage.all(Place).values()
    places = []
    places_id = []
    keys_status = (
        all([
            'states' in data and type(data['states']) is list,
            'states' in data and len(data['states'])
        ]),
        all([
            'cities' in data and type(data['cities']) is list,
            'cities' in data and len(data['cities'])
        ]),
        all([
            'amenities' in data and type(data['amenities']) is list,
            'amenities' in data and len(data['amenities'])
        ])
    )
    if keys_status[0]:
        for state_id in data['states']:
            if not state_id:
                continue
            state = storage.get(State, state_id)
            if not state:
                continue
            for city in state.cities:
                new_places = []
                if storage_t == 'db':
                    new_places = list(
                        filter(lambda x: x.id not in places_id, city.places)
                    )
                else:
                    new_places = []
                    for place in all_places:
                        if place.id in places_id:
                            continue
                        if place.city_id == city.id:
                            new_places.append(place)
                places.extend(new_places)
                places_id.extend(list(map(lambda x: x.id, new_places)))
    if keys_status[1]:
        for city_id in data['cities']:
            if not city_id:
                continue
            city = storage.get(City, city_id)
            if city:
                new_places = []
                if storage_t == 'db':
                    new_places = list(
                        filter(lambda x: x.id not in places_id, city.places)
                    )
                else:
                    new_places = []
                    for place in all_places:
                        if place.id in places_id:
                            continue
                        if place.city_id == city.id:
                            new_places.append(place)
                places.extend(new_places)
    del places_id
    if all([not keys_status[0], not keys_status[1]]) or not data:
        places = all_places
    if keys_status[2]:
        amenity_ids = []
        for amenity_id in data['amenities']:
            if not amenity_id:
                continue
            amenity = storage.get(Amenity, amenity_id)
            if amenity and amenity.id not in amenity_ids:
                amenity_ids.append(amenity.id)
        del_indices = []
        for place in places:
            place_amenities_ids = list(map(lambda x: x.id, place.amenities))
            if not amenity_ids:
                continue
            for amenity_id in amenity_ids:
                if amenity_id not in place_amenities_ids:
                    del_indices.append(place.id)
                    break
        places = list(filter(lambda x: x.id not in del_indices, places))
    result = []
    for place in places:
        obj = place.to_dict()
        if 'amenities' in obj:
            del obj['amenities']
        result.append(obj)
    return jsonify(result)
